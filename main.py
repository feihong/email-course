from gmail import SimpleEmail, get_unread_messages, send, reply
from gmail import _convert, _simplify, _get_messages, service


if __name__ == '__main__':
    for msg in get_unread_messages():
        print(msg.sender)
        print(msg.subject)
        print('='*75)

    # reply(orig=msg, response=SimpleEmail(
    #     body='This is my courteous reply'
    # ))

    # for msg in [_convert(m) for m in _get_messages()]:
    #     print(msg)
    #     print('='*75)
