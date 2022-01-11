import socket
import threading
import errno
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from common.error import *
from common.util import *
from common.user import User
from common.udp_socket import UDP_Socket
from common.tcp_socket import TCP_Socket
from common.protocol import Protocol
from database import Database


IP = socket.gethostbyname(socket.gethostname())
TCP_ADDR = (IP, TCP_Socket.TCP_PORT)
UDP_ADDR = (IP, UDP_Socket.UDP_PORT)


tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_sock.bind(TCP_ADDR)

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(UDP_ADDR)

tcp_socket = TCP_Socket(socket=tcp_sock, address=TCP_ADDR)
udp_socket = UDP_Socket(socket=udp_sock, address=UDP_ADDR)


class Registry:
    online_clients = []
    lock = threading.Lock()
    tcp_socket: TCP_Socket = None
    udp_socket: UDP_Socket = None

    def __init__(self, tcp_socket, udp_socket):
        Registry.tcp_socket = tcp_socket
        Registry.udp_socket = udp_socket        
        self.db = Database()
        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()
        udp_thread = threading.Thread(target=self.listen_udp)
        udp_thread.start()
        self.db.set_offline()
        
        with open('logfile.log', 'w'):
            pass
        logmessage = 'REGISTRY is starting'
        self.tcp_socket.log(logmessage)


    def register(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        password = packet_data['password']
        chatport = packet_data['chatport']
        with Registry.lock:
            try:
                user = User(username, password, client_socket.address, datetime.now(),
                            int(chatport), online=True)
                self.db.register(**user.__dict__)
                Registry.online_clients.append(user)
                obj = {'user': user, 'request': 'REGISTER',
                       'msg': 'The registration is complete'}
                client_socket.send('OK', obj)
            except UserAlreadyExistsException:
                obj = {'request': 'REGISTER',
                       'msg': 'This username is already used.', 'username': user.username}
                client_socket.send('REJECT', obj)

    def login(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        password = packet_data['password']
        chatport = packet_data['chatport']
        with Registry.lock:
            try:
                if check_user(Registry.online_clients, username):
                    obj = {
                        'request': 'LOGIN', 'msg': 'User is logged in another instance', 'username': username}
                    client_socket.send('REJECT', obj)
                else:
                    user = User(**self.db.login(username, password,
                            client_socket.address, chatport))
                    Registry.online_clients.append(user)
                    obj = {'user': user, 'request': 'LOGIN',
                           'msg': 'Login successful'}
                    client_socket.send('OK', obj)
            except WrongPasswordException:
                obj = {'request': 'LOGIN',
                       'msg': 'Invalid password. Please try again', 'username': username}
                client_socket.send(
                    'REJECT', obj)
            except UserNotExistsException:
                obj = {'request': 'LOGIN',
                       'msg': 'Invalid username. Please register first', 'username': username}
                client_socket.send(
                    'REJECT', obj)

    def logout(self, packet_data, client_socket: TCP_Socket):
        user = packet_data['user']
        with Registry.lock:
            try:
                if user is not None:
                    self.db.logout(user.username)
                    obj = {'request': 'LOGOUT', 'msg': 'Logout successful'}
                    user.online = False
                    remove_user_by_username(Registry.online_clients, user.username)
                    client_socket.send('OK', obj)
                else:
                    raise UserIsNotLoggedInException
            except UserIsNotLoggedInException:
                obj = {'request': 'LOGOUT',
                       'msg': 'User is currently not signed in'}
                client_socket.send('REJECT', obj)

    def search(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        with Registry.lock:
            try:
                address = self.db.chat_address(username)
                obj = {'request': 'SEARCH', 'msg': 'User found',
                       'address': address, 'username': username}
                client_socket.send('OK', obj)

            except UserNotExistsException:
                obj = {'request': 'SEARCH',
                       'msg': 'User not found', 'username': username}
                client_socket.send('NOTFOUND', obj)

    def chat_request(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        with Registry.lock:
            try:
                chat_address = self.db.chat_address(username)
                obj = {'request': 'CHATREQUESTREG', 'msg': 'User found',
                       'address': chat_address, 'username': username}
                client_socket.send('OK', obj)
            except UserNotExistsException:
                obj = {'request': 'CHATREQUESTREG', 'msg': 'User not found', 'username': username}
                client_socket.send('NOTFOUND', obj)

    def listen_tcp(self):
        self.tcp_socket.socket.listen()
        print(f"[LISTENING] Server is listening on {TCP_ADDR}")
        while True:
            client_socket, client_address = self.tcp_socket.socket.accept()
            client_socket = TCP_Socket(
                socket=client_socket, address=client_address)
            # Create new thread for every incoming tcp connection
            client_thread = threading.Thread(
                target=self.receive_packet_tcp, args=(client_socket,))
            client_thread.start()

    def receive_packet_tcp(self, client_socket: TCP_Socket):
        connected = True

        while connected:
            try:
                packet_header, packet_data = client_socket.receive_message()
                username = packet_data['username']
                logmessage = Protocol.logmessages['REQUEST'][packet_header]['registry']
                if packet_header == 'REGISTER':
                    self.register(packet_data, client_socket)
                    self.tcp_socket.log(logmessage % username)
                elif packet_header == 'LOGIN':
                    self.login(packet_data, client_socket)
                    self.tcp_socket.log(logmessage % username)
                elif packet_header == 'LOGOUT':
                    self.logout(packet_data, client_socket)
                    self.tcp_socket.log(logmessage % username)
                elif packet_header == 'SEARCH':
                    self.search(packet_data, client_socket)
                    self.tcp_socket.log(logmessage % (packet_data['user'], username))
                elif packet_header == 'CHATREQUESTREG':
                    self.chat_request(packet_data, client_socket)
                    self.tcp_socket.log(logmessage % username)
                    

            except IOError as e:
                if e.errno == errno.EBADF:
                    print('Client socket is closed')
                    sys.exit()

    def active(self, user):
        while True:
            now = datetime.now()
            delta = (now - user.last_active).total_seconds()
            if delta > 20:
                with Registry.lock:
                    self.db.update_field(user.username, online=False)
                    user.online = False
                    Registry.online_clients.remove(user)
                    sys.exit()

    def listen_udp(self):
        while True:
            packet_header, packet_data = self.udp_socket.receive_message()
            username = packet_data['username']
            user: User = check_user(Registry.online_clients, username)
            # if user doesnt have a thread that is already created make a thread for that user
            if user and not user.thread_active:
                user_thread = threading.Thread(
                    target=self.active, args=(user,))
                user_thread.start()
                user.thread_active = True
            # in each HELLO message reset the timer
            if user and packet_header == 'HELLO':
                print(f'Received udp packet with the header {packet_header}')
                user.last_active = datetime.now()
                logmessage = Protocol.logmessages['REQUEST']['HELLO']['registry'] % user.username
                self.tcp_socket.log(logmessage)


def main():
    Registry(tcp_socket=tcp_socket, udp_socket=udp_socket)


if __name__ == '__main__':
    main()
