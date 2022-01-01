class User:
    def __init__(self, username, password,  address, last_active, chatport, busy=False, thread_active=False, port=None, online=False):
        self.username = username
        self.password = password
        self.address = address
        self.last_active = last_active
        self.chatport = chatport
        self.busy = busy
        self.thread_active = thread_active
        self.port = port
        self.online = online


                    
