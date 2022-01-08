import errno
import time
import socket
import threading
import sys
from common.tcp_socket import TCP_Socket
from common.udp_socket import UDP_Socket
from common.our_sock import Socket
from common.util import *

port_list = range(5000, 6000, 42)

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

for port in port_list:
    try:
        chat_sock.bind((IP, port))
        print(f'Client is listening on {(IP,port)}')
        break
    except:
        print(f'port {port} is unavaliable trying another port')

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tcp_socket = TCP_Socket(socket=tcp_sock, address=tcp_sock.getsockname())
udp_socket = UDP_Socket(socket=udp_sock, address=UDP_ADDR)
chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())

resume = True
loop = True
chat = False

user_input = None
chat_request = False
chat_end = None
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
            except OSError as e:
                print('\nConnection to server is closed forcely')
                global loop
                with lock:
                    loop = False
                sys.exit()

            except Exception as e:
                with lock:
                    resume = True
                print(e)

    def listen_udp(self):
        while True:
            try:
                self.udp_socket.receive_message()
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
            if not self.user:
                username = input('> username: ')
                password = input('> password: ')
                obj = {'username': username, 'password': password, 'chatport': port}
                if not self.user:
                    self.tcp_socket.send(header, obj)
            else:
                print('You are currently logged in')
                resume = True
        elif header == 'LOGOUT':
            self.tcp_socket.send('LOGOUT', self.user)
        elif header == 'SEARCH':
            if self.user:
                username = input('> Enter the username of the user you want to search: ')
                obj = {'username': username}
                self.tcp_socket.send('SEARCH', obj)
            else:
                print('> To search a user you should be signed in')
                resume = True
        elif header == 'CHATREQUEST':
            if self.user:
                username = input(
                    '> Enter the username of the user you want to chat: ')
                obj = {'username': username}
                self.tcp_socket.send('CHATREQUESTREG', obj)
            else:
                print('> To send a chat request you should be signed in')
                resume = True

class PeerServer(Socket):
    def __init__(self, chat_socket):
        self.tcp_socket: TCP_Socket = chat_socket
        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()

    def chat(self):
        global chat
        global resume
        global chat_end
        while chat:
            message = input('> ')
            chat_end = message
            if message == 'exit':
                with lock:
                    chat = False
                    resume = True
                obj = {'msg' : f'{self.user.username} closed chat connection'}
                self.chat_socket.send('REJECT', obj)
                self.chat_socket = None
                self.user.busy = False
                chat_end = None
                break

            obj = {'msg': message}
            if self.chat_socket:
                self.chat_socket.send('CHAT', obj)

    def send_chat_request(self):
        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_sock.connect(self.peer_address)
        self.chat_socket = TCP_Socket(
            socket=chat_sock, address=chat_sock.getsockname())
        obj = {'username': self.user.username, 'request': 'CHATREQUEST', 'address' : self.tcp_socket.socket.getsockname()}
        self.chat_socket.send('CHATREQUEST', obj)

    def receive_packet_chat_socket(self, client_socket: TCP_Socket):
        global chat
        global resume
        global user_input
        global chat_request
        resume = False
        while True:
            try:
                packet_header, packet_data = client_socket.receive_message()
                with lock:
                    if packet_header == 'CHATREQUEST':
                        chat_request = True
                        chat_socket_address = packet_data['address']
                        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        chat_sock.connect(chat_socket_address)
                        self.chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())
                        if self.user.busy:
                            obj = {
                                'msg': 'User is currently chatting with another person'}
                            resume = True
                            self.chat_socket.send('BUSY', obj)
                            chat_request = False
                        else:
                            username = packet_data['username']
                            print(f'\nUser {username} wants to chat with you [Y/N]: ', end='')
                            user_input = None
                            accept = user_input
                            answers = ['y', 'n']
                            while accept not in answers:
                                if not user_input:
                                    continue
                                elif user_input and not accept:
                                    accept = user_input.lower()
                                else:
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
                                    'msg': f'\n{self.user.username} rejected to chat'}
                                resume = True
                                self.chat_socket.send('REJECT', obj)
                            
                            chat_request = False

                    elif packet_header in Socket.RESPONSE_HEADERS:
                        message = packet_data['msg']
                        if packet_header == 'OK':
                            self.user.busy = True
                            self.user.peer_name = packet_data['username']
                            chat = True
                        if packet_header == 'REJECT' or packet_header == 'BUSY':
                            print(message)
                            if chat:
                                print('> Type operation that you want to make: ', end='')
                            resume = True
                            chat = False
                            self.chat_socket = None
                            self.user.busy = False
                            sys.stdout.flush()
                            sys.exit()

                    elif packet_header == 'CHAT':
                        message = packet_data['msg']
                        print(f'{self.user.peer_name}: {message}')
                        print('> ', end='')
                        sys.stdout.flush()

            except IOError as e:
                if e.errno == errno.EBADF:
                    with lock:
                        resume = True
                        chat = False
                        sys.exit()


            except Exception as e:
                print(e)

    def listen_tcp(self):
        self.tcp_socket.socket.listen()
        while True:
            client_socket, client_address = self.tcp_socket.socket.accept()
            client_socket = TCP_Socket(
                socket=client_socket, address=client_address)
            client_thread = threading.Thread(target=self.receive_packet_chat_socket, args=(client_socket, ))
            client_thread.start()


def main():
    global user_input
    global chat_end
    peer_server = PeerServer(chat_socket=chat_socket)
    peer = Peer(tcp_socket=tcp_socket,
                    udp_socket=udp_socket, peer_server=peer_server)

    while loop:
        if resume:
            user_input = input(
                '> Type operation that you want to make: ').upper() if not chat_end else chat_end.upper()
            if chat_end:
                chat_end = None
            if user_input not in Socket.REQUEST_HEADERS and not chat_request:
                print('Invalid operation')
                continue
            else:
                peer.make_request(user_input)
        if chat:
            peer.peer_server.chat()
    sys.exit()


if __name__ == '__main__':
    main()
