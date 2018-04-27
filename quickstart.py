"""
Shows basic usage of the Gmail API.

Lists the user's Gmail labels.
"""
import functools
import base64
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import attr


@attr.s
class SimpleEmail:
    id = attr.ib(default='')
    thread_id = attr.ib(default='')
    label_ids = attr.ib(default=attr.Factory(list))
    sender = attr.ib(default='')
    subject = attr.ib(default='')
    body = attr.ib(default='')


# Setup the Gmail API
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))

def get_message_ids():
    results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
    messages = results.get('messages', [])
    for msg in messages:
        yield msg['id']

def get_messages():
    msg_resource = service.users().messages()

    for msg_id in get_message_ids():
        yield msg_resource.get(userId='me', id=msg_id).execute()

def simplify(msg):
    headers = {d['name']: d['value'] for d in msg['payload']['headers']}

    result = SimpleEmail(
        id=msg['id'],
        thread_id=msg['threadId'],
        label_ids=msg['labelIds'],
        sender=headers['From'],
        subject=headers['Subject'])

    for part in msg['payload']['parts']:
        if part['mimeType'] == 'text/plain':
            result.body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

    return result


messages = [m for m in get_messages()]
for msg in messages:
    print(msg)

print(len(messages))
