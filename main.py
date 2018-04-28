from gmail import get_unread_messages


if __name__ == '__main__':
    for msg in get_unread_messages():
        print(msg)
        print('='*75)
