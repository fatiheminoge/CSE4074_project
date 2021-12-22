from datetime import datetime
import sys
import threading

class User:
    def __init__(self, name, password,  client_address, last_active = 0,port = None, status = False):
        self.name = name
        self.password = password
        self.last_active = last_active
        self.port = port
        self.status = status
        self.client_address = client_address
    
    def active(self):
        now = datetime.now()
        delta = now - self.last_active
        if delta.seconds() > 200:
            with threading.Lock():
                self.status = False
            sys.exit() # close thread 

