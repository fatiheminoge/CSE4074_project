import errno
import time
import socket
import threading
import sys

from tcp_socket import TCP_Socket
from udp_socket import UDP_Socket
from sock import Socket
from util import *

port = input('port no: ')

lock = threading.Lock()
# getting local ip automatically
SERVER = socket.gethostbyname('localhost')
IP = socket.gethostbyname('localhost')
TCP_ADDR = (SERVER, Socket.TCP_PORT)
UDP_ADDR = (SERVER, Socket.UDP_PORT)

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect(TCP_ADDR)

chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
chat_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
chat_sock.bind((IP, int(port)))

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tcp_socket = TCP_Socket(socket=tcp_sock, address=tcp_sock.getsockname())
udp_socket = UDP_Socket(socket=udp_sock, address=UDP_ADDR)
chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())

resume = True
loop = True
chat = False


class Peer(Socket):

    def __init__(self, tcp_socket, udp_socket, peer_server):
        """
        Threads are created to send/receive tcp and udp messages sent from the registry
        Args:
            tcp_socket ([TCP_Socket])
            udp_socket ([UDP_Socket])
            client_chat ([PeerServer])
        """

        super().__init__()
        self.tcp_socket: TCP_Socket = tcp_socket
        self.udp_socket: UDP_Socket = udp_socket
        self.user = None
        self.peer_server: PeerServer = peer_server

        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()
        udp_thread = threading.Thread(target=self.send_hello)
        udp_thread.start()

    def listen_tcp(self):
        global resume
        while True:
            try:
                packet_header, packet_data = self.tcp_socket.receive_message()
                with lock:
                    request = packet_data['request']
                    if request == 'LOGIN' or request == 'REGISTER':
                        if packet_header == 'OK':
                            user = packet_data['user']
                            self.user = user
                            self.peer_server.user = user
                        message = packet_data['msg']
                        print(message)
                        resume = True
                    elif request == 'LOGOUT':
                        if packet_header == 'OK':
                            self.user = None
                        message = packet_data['msg']
                        print(message)
                        resume = True
                    elif request == 'SEARCH':
                        if packet_header == 'OK':
                            user_address = packet_data['address']
                            print(user_address)
                        message = packet_data['msg']
                        print(message)
                        resume = True
                    elif request == 'CHATREQUESTREG':
                        if packet_header == 'OK':
                            user_address = packet_data['address']
                            self.peer_server.peer_address = user_address
                            self.peer_server.send_chat_request()
                        else:
                            message = packet_data['msg']
                            resume = True   
                            print(message)
                        pass
            except ConnectionResetError as e:
                print('\nConnection to server is closed forcely')
                global loop
                loop = False
                sys.exit()

            except Exception as e:
                resume = True
                print(e)

    def listen_udp(self):
        while True:
            try:
                packet_header, packet_data = self.udp_socket.receive_message()
            except:
                pass

    def send_hello(self):
        while True:
            if self.user is not None:
                obj = {'username': self.user.username}
                self.udp_socket.send('HELLO', obj)
                time.sleep(60)

    def make_request(self, header):
        global resume
        resume = False
        if header == 'REGISTER' or header == 'LOGIN':
            username = input('>username: ')
            password = input('>password: ')
            obj = {'username': username, 'password': password, 'chatport': port}
            self.tcp_socket.send(header, obj)
        elif header == 'LOGOUT':
            self.tcp_socket.send('LOGOUT', self.user)
        elif header == 'SEARCH':
            username = input('>username: ')
            obj = {'username': username}
            self.tcp_socket.send('SEARCH', obj)
        elif header == 'CHATREQUEST':
            username = input(
                '>Enter the username of the user you want to chat: ')
            obj = {'username': username}
            self.tcp_socket.send('CHATREQUESTREG', obj)
        else:
            pass


class PeerServer(Socket):
    def __init__(self, chat_socket):
        self.tcp_socket: TCP_Socket = chat_socket
        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()

    def chat(self):
        while True:
            message = input('> ')
            obj = {'msg': message}
            self.chat_socket.send('CHAT', obj)

    def send_chat_request(self):
        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_sock.connect(self.peer_address)
        self.chat_socket = TCP_Socket(
            socket=chat_sock, address=chat_sock.getsockname())
        obj = {'username': self.user.username, 'request': 'CHATREQUEST', 'address' : self.tcp_socket.socket.getsockname()}
        self.chat_socket.send('CHATREQUEST', obj)

    def receive_packet(self, client_socket: TCP_Socket):
        global chat
        global resume
        resume = False
        while True:
            try:
                packet_header, packet_data = client_socket.receive_message()
                with lock:
                    if packet_header == 'CHATREQUEST':
                        chat_socket_address = packet_data['address']
                        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        chat_sock.connect(chat_socket_address)
                        self.chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())
                        if self.user.busy:
                            obj = {
                                'msg': 'User is currently chatting with another person'}
                            resume = True
                            self.chat_socket.send('BUSY', obj)
                        else:
                            username = packet_data['username']
                            sys.stdout.write('')
                            print(f'\nUser {username} wants to chat with you [Y/N]:', end=' ')
                            accept = input().lower()
                            while accept != 'y' and accept != 'n': 
                                accept = input('Invalid option enter [Y/N]: ').lower()

                            accept = True if accept == 'y' else False
                            if accept:
                                self.user.busy = True
                                self.user.peer_name = username
                                obj = {
                                    'msg': f'{self.user.username} accepted to chat', 'username' : self.user.username}
                                chat = True
                                self.chat_socket.send('OK', obj)
                            else:
                                obj = {
                                    'msg': f'{self.user.username} rejected to chat'}
                                resume = True
                                self.chat_socket.send('REJECT', obj)

                    elif packet_header in Socket.RESPONSE_HEADERS:
                        message = packet_data['msg']
                        if packet_header == 'OK':
                            self.user.busy = True
                            self.user.peer_name = packet_data['username']
                            chat = True
                        if packet_header == 'REJECT' or packet_header == 'BUSY':
                            resume = True

                    elif packet_header == 'CHAT':
                        message = packet_data['msg']
                        print(f'\n{self.user.peer_name}: {message}')

            except IOError as e:
                if e.errno == errno.EBADF:
                    print('Client socket is closed')
                    sys.exit()


            except Exception as e:
                print(e)
                pass

    def listen_tcp(self):
        print(self.tcp_socket.socket.getsockname())
        self.tcp_socket.socket.listen()
        while True:
            client_socket, client_address = self.tcp_socket.socket.accept()
            client_socket = TCP_Socket(
                socket=client_socket, address=client_address)
            client_thread = threading.Thread(target=self.receive_packet, args=(client_socket, ))
            client_thread.start()
    


def main():
    global resume
    peer_server = PeerServer(chat_socket=chat_socket)
    peer = Peer(tcp_socket=tcp_socket,
                    udp_socket=udp_socket, peer_server=peer_server)

    while loop:
        if resume:
            header = input(
                '>Type operation that you want to make: ').upper()
            if header not in Socket.REQUEST_HEADERS:
                print('Invalid operation')
                continue
            else:
                peer.make_request(header)
        if chat:
            peer.peer_server.chat()
    sys.exit()


if __name__ == '__main__':
    main()
