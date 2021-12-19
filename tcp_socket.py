from util import *
from user import User
import threading

class TCP_Socket:

    """
    tcp socket class
    Args:
        - clients, socket
    """
    def __init__(self, clients, socket):
        self.clients = clients
        self.socket = socket

    def login(self):
        # New user username check
        username, password = self.packet_data['username'].decode('utf-8'), self.packet_data['password'].decode('utf-8')
        user: User = check_user(self.clients, username)
        if user:
            user_acceptence = check_password(user, password)
            if user_acceptence:
                with threading.Lock():
                    user.status = True
            else:
                self.client_socket.send(b'Invalid password. Please try again')

            self.client_socket.send(b'Connected to chatroom')
        else:
            self.register(username, password)

    def register(self, username, password):
        user = User(username, password, self.client_address, status=True)
        with threading.Lock():
            self.clients.append(user)
        self.client_socket.send(b'The registeration is complete')

    def logout(self):
        username = self.packet_data['username']
        user: User = check_user(self.clients, username)
        with threading.Lock():
            user.status = False
        user.client_socket.send(b'Logout')
        user.client_socket.close()