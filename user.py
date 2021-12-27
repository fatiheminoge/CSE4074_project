from datetime import datetime
import sys


class User:
    def __init__(self, username, password,  address, last_active, chatport, busy=False, thread_active=False, port=None, status=False):
        self.username = username
        self.password = password
        self.address = address
        self.last_active = last_active
        self.chatport = chatport
        self.busy = busy
        self.thread_active = thread_active
        self.port = port
        self.status = status

    def active(self, lock):
        while True:
            now = datetime.now()
            delta = (now - self.last_active).total_seconds()
            if delta > 200:
                with lock:
                    self.status = False
                    sys.exit()
