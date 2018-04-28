import base64
import email
from email.message import EmailMessage
import mimetypes
from pathlib import Path
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import attr


@attr.s
class SimpleEmail:
    """
    A simplified email object.

    """
    id = attr.ib(default='')
    thread_id = attr.ib(default='')
    message_id = attr.ib(default='')
    label_ids = attr.ib(default=attr.Factory(list))
    sender = attr.ib(default='')
    recipient = attr.ib(default='')
    subject = attr.ib(default='')
    body = attr.ib(default='')
    # List of attachment names
    attachments = attr.ib(default=attr.Factory(list))


# Setup the Gmail API
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))


def get_unread_messages():
    return [_simplify(msg) for msg in _get_messages()]


def _get_message_ids():
    results = (service.users().messages()
        .list(userId='me', labelIds=['UNREAD']).execute())
    messages = results.get('messages', [])
    for msg in messages:
        yield msg['id']


def _get_message_requests():
    msg_resource = service.users().messages()
    for msg_id in _get_message_ids():
        yield msg_resource.get(userId='me', id=msg_id, format='raw')


def _get_messages():
    """
    Retrieve all unread messages using a batch request.

    Todo: Allow this function to retrieve more than 100 messages (batch requests
    limit is 100)

    """
    responses = []
    def callback(_id, response, _exception):
        # todo: do something with exceptions
        responses.append(response)

    batch_req = service.new_batch_http_request(callback)
    for req in _get_message_requests():
        batch_req.add(req)

    batch_req.execute()     # execute() returns None
    return responses


def _convert(msg):
    """
    Convert gmail message dict to EmailMessage object.

    """
    msg_bytes = base64.urlsafe_b64decode(msg['raw'])
    # Have to specify policy, otherwise we get a Message object instead of an
    # EmailMessage object.
    return email.message_from_bytes(msg_bytes, policy=email.policy.default)


def _simplify(msg):
    """
    Convert gmail message dict to SimpleEmail object.

    """
    result = SimpleEmail(
        id=msg['id'],
        thread_id=msg['threadId'],
        label_ids=msg['labelIds'],
    )

    email_msg = _convert(msg)
    result.message_id = email_msg['Message-Id']
    result.subject = email_msg['Subject']
    result.sender = email_msg['From']
    result.body = email_msg.get_body('plain').get_content()
    result.attachments = [part.get_filename() for part in
                            email_msg.iter_attachments()]
    return result

def _get_email_message(sm: SimpleEmail):
    em = EmailMessage()
    em.set_content(sm.body)
    em['Subject'] = sm.subject
    em['To'] = sm.recipient
    em['From'] = sm.sender
    for att in sm.attachments:
        path = Path(att)
        content_type, _encoding = mimetypes.guess_type(path.name)
        maintype, subtype = content_type.split('/', 1)
        em.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name)

    return em


def _send_email_message(em: EmailMessage):
    raw = base64.urlsafe_b64encode(em.as_bytes()).decode('ascii')
    message = (service.users().messages().send(userId='me', body={'raw': raw})
               .execute())
    return message


def send(sm: SimpleEmail):
    em = _get_email_message(sm)
    return _send_email_message(em)

def reply(orig: SimpleEmail, response: SimpleEmail):
    response.subject = 'Re: ' + orig.subject
    response.sender, response.recipient = orig.recipient, orig.sender
    em = _get_email_message(response)
    em['References'] = orig.message_id
    em['In-Reply-To'] = orig.message_id

    raw = base64.urlsafe_b64encode(em.as_bytes()).decode('ascii')
    body = {
        'raw': raw,
        'threadId': orig.thread_id,
    }
    message = (service.users().messages().send(userId='me', body=body)
               .execute())
    return message
