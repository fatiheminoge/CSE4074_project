from datetime import datetime

class User:
    def __init__(self, username, password,  client_address, last_active ,port = None, status = False):
        self.username = username
        self.password = password
        self.last_active = last_active
        self.port = port
        self.status = status
        self.client_address = client_address


