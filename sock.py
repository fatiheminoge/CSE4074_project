class Socket:
    FORMAT = 'utf-8'
    REQUEST_HEADERS = [
    'REGISTER', 'LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'SEARCH'
    ]
    RESPONSE_HEADERS = [
        'OK', 'REJECT', 'BUSY', 'INVALID', 'NOTFOUND'
    ]
    HEADER_LENGTH = 16
    UDP_PACKET_SIZE = 1024
    TCP_PORT = 2424
    UDP_PORT = 4242

    def __init__(self) -> None:
        pass

    def create_message(self):
        pass

    def parse_message(self):
        pass