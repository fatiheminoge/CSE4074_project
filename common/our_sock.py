class Socket:
    FORMAT = 'utf-8'
    REQUEST_HEADERS = [
        'REGISTER', 'LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'SEARCH', 'CHATREQUESTREG', 'MULTICHATREQUESTREG' ,'MULTICHATREQUEST','CHATSTATE', 'CHAT','NEWPEER','MULTICHAT'
    ]
    RESPONSE_HEADERS = [
        'OK', 'MULTIOK','REJECT','MULTIREJECT', 'MULTIBUSY','BUSY', 'INVALID', 'NOTFOUND'
    ]
    HEADER_LENGTH = 32
    UDP_PACKET_SIZE = 1024
    TCP_PORT = 2424
    UDP_PORT = 4242

    def __init__(self) -> None:
        pass

    def create_message(self):
        pass

    def parse_message(self):
        pass