import base64
import email
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
    label_ids = attr.ib(default=attr.Factory(list))
    sender = attr.ib(default='')
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
    results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
    messages = results.get('messages', [])
    for msg in messages:
        yield msg['id']


def _get_messages():
    msg_resource = service.users().messages()
    for msg_id in _get_message_ids():
        yield msg_resource.get(userId='me', id=msg_id, format='raw').execute()


def _simplify(msg):
    """
    Convert gmail message dict to SimpleEmail object.

    """
    msg_bytes = base64.urlsafe_b64decode(msg['raw'])
    # Have to specify policy, otherwise we get a Message object instead of an
    # EmailMessage object.
    email_msg = email.message_from_bytes(msg_bytes, policy=email.policy.default)
    result = SimpleEmail(
        id=msg['id'],
        thread_id=msg['threadId'],
        label_ids=msg['labelIds'])

    result.subject = email_msg['Subject']
    result.sender = email_msg['From']
    result.body = email_msg.get_body('plain').get_content()
    result.attachments = [part.get_filename() for part in
                            email_msg.iter_attachments()]
    return result
