import socket
import threading
import errno
import sys
from datetime import datetime

from tcp_socket import TCP_Socket
from udp_socket import UDP_Socket
from user import User
from util import *

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
    clients = []
    online_clients = []
    lock = threading.Lock()
    tcp_socket: TCP_Socket = None
    udp_socket: UDP_Socket = None

    def __init__(self, tcp_socket, udp_socket):
        Registry.tcp_socket = tcp_socket
        Registry.udp_socket = udp_socket
        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()
        udp_thread = threading.Thread(target=self.listen_udp)
        udp_thread.start()

    def register(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        password = packet_data['password']

        with Registry.lock:
            if not check_user(Registry.clients, username):
                user = User(username, password, client_socket.address,
                            datetime.now(), status=True)
                Registry.clients.append(user)
                Registry.online_clients.append(user)
                obj = {'user': user, 'request': 'REGISTER',
                       'msg': 'The registration is complete'}
                client_socket.send('OK', obj)
            else:
                obj = {'request': 'LOGIN', 'msg': 'This username is already used.'}
                client_socket.send('REJECT', obj)

    def login(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        password = packet_data['password']
        with Registry.lock:
            user = check_user(Registry.clients, username)
            if (user is not None) and (check_password(user, password)):
                user.status = True
                user.last_active = datetime.now()
                user.address = client_socket.address
                Registry.online_clients.append(user)
                obj = {'user': user, 'request': 'LOGIN',
                       'msg': 'Login successful'}
                client_socket.send('OK', obj)
            elif user is None:
                obj = {'request': 'LOGIN', 'msg': 'Invalid username. Please register first'}
                client_socket.send(
                    'REJECT', obj)
            else:
                obj = {'request': 'LOGIN', 'msg': 'Invalid password. Please try again'}
                client_socket.send(
                    'REJECT', obj)

    def logout(self, user, client_socket: TCP_Socket):            
        with Registry.lock:
            if user is not None:
                user = check_user(Registry.online_clients, user.username)
                user.status = False
                Registry.online_clients.remove(user)
                obj = {'request': 'LOGOUT', 'msg': 'Logout successful'}
                client_socket.send('OK', obj)
            else:
                obj = {'request': 'LOGOUT', 'msg': 'User is currently not signed in'}
                client_socket.send('REJECT', obj)

    def search(self, packet_data, client_socket: TCP_Socket):
        username = packet_data['username']
        with Registry.lock:
            user = check_user(Registry.online_clients, username)
            if user is not None:
                obj = {'request' : 'SEARCH', 'msg' : 'User found', 'address' : user.address}
                client_socket.send('OK', obj)
            else:
                obj = {'request': 'SEARCH', 'msg' : 'User not found'}
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
                if packet_header == 'REGISTER':
                    self.register(packet_data, client_socket)
                elif packet_header == 'LOGIN':
                    self.login(packet_data, client_socket)
                elif packet_header == 'LOGOUT':
                    self.logout(packet_data, client_socket)
                elif packet_header == 'SEARCH':
                    self.search(packet_data, client_socket)
                else:
                    pass

            except IOError as e:
                if e.errno == errno.EBADF:
                    print('Client socket is closed')
                    sys.exit()

    def listen_udp(self):
        while True:
            packet_header, packet_data = self.udp_socket.receive_message()
            username = packet_data['username']
            user: User = check_user(Registry.online_clients, username)
            # if user doesnt have a thread that is already created make a thread for that user
            if user and not user.thread_active:
                user_thread = threading.Thread(target=user.active, args=(Registry.lock,))
                user_thread.start()
                user.thread_active = True
            # in each HELLO message reset the timer
            if user and packet_header == 'HELLO':
                print(f'Received udp packet with the header {packet_header}')
                user.last_active = datetime.now()


def main():
    Registry(tcp_socket=tcp_socket, udp_socket=udp_socket)


if __name__ == '__main__':
    main()
