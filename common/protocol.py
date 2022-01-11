class Protocol:
    FORMAT = 'utf-8'
    REQUEST_HEADERS = [
        'REGISTER', 'LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'SEARCH', 'CHATREQUESTREG', 'CHAT'
    ]
    RESPONSE_HEADERS = [
        'OK', 'REJECT', 'BUSY', 'INVALID', 'NOTFOUND'
    ]
    HEADER_LENGTH = 16
    UDP_PACKET_SIZE = 1024
    TCP_PORT = 2424
    UDP_PORT = 4242
    logmessages = {
        'REQUEST':
            {
                'REGISTER': {'registry': 'Received REGISTER request from user: %s', 'client': 'Client %s made a REGISTER request to registry'},
                'LOGIN': {'registry': 'Received LOGIN request from user: %s', 'client': 'User: %s made a LOGIN request to registry'},
                'LOGOUT': {'registry': 'Received LOGOUT request from user: %s', 'client': 'User: %s made a LOGOUT request to registry'},
                'HELLO': {'registry': 'Received HELLO request from User: %s', 'client': 'User: %s made a HELLO request to registry'},
                'CHATREQUEST': {'client': 'User: %s sent a CHATREQUEST to user %s'},
                'SEARCH': {'registry': 'User: %s sent a SEARCH request for user %s', 'client': 'User: %s made a SEARCH request for the user: %s to registry'},
                'CHATREQUESTREG': {'registry': 'Received CHATREQUESTREG request from user: %s', 'client': 'User: %s made a CHATREQUESTREG for the user: %s to registry'},
                'CHAT': {'client': 'User: %s sent a message to user: %s'}
            },

        'RESPONSE':
            {
                'OK':
                    {
                        'registry': '',
                        'client': {
                            'REGISTER': 'User: %s, successfully registered %s',
                            'LOGIN': 'User: %s, successfully logged in %s',
                            'LOGOUT': 'User: %s, successfully logged out %s',
                            'SEARCH': 'User: %s, successfully found the user %s',
                            'CHATREQUESTREG': 'User: %s, successfully found the user %s',
                            'CHATREQUEST': 'User: Chat with the user %s is accepted %s',
                            'CHAT': 'User: %s, accepted to chat with %s'
                        }
                    },
                'REJECT':
                    {
                        'registry': '',
                        'client':
                            {
                                'REGISTER': 'User: %s, couldn\'t registered because %s',
                                'LOGIN': 'User: %s, couldn\'t logged in because %s',
                                'LOGOUT': 'User: %s, couldn\'t logged out because %s',
                                'CHAT': 'User: %s, rejected to chat with %s',
                                'CHATREQUEST': 'User: %s, rejected to chat with %s'
                            }
                    },
                'BUSY': {
                    'registry': '',
                        'client':
                        {
                            'CHAT': 'User: %s, user %s is busy'
                        }
                },
                'INVALID': {'registry': '', 'client': ''},
                'NOTFOUND':
                    {
                        'registry': '',
                        'client': {
                            'SEARCH': 'User: %s, couldn\'t be found %s',
                            'CHATREQUESTREG': 'User: %s, couldn\'t be found %s'
                        }
                        }
            },
            'CONNECTION': 'Peer with the address %s connected to %s',

    }

    def __init__(self) -> None:
        pass

    def create_message(self):
        pass

    def parse_message(self):
        pass
