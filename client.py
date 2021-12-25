import time
import socket
import threading
import sys

from tcp_socket import TCP_Socket
from udp_socket import UDP_Socket
from sock import Socket
from util import *

lock = threading.Lock()
# getting local ip automatically
SERVER = socket.gethostbyname(socket.gethostname())
TCP_ADDR = (SERVER, Socket.TCP_PORT)
UDP_ADDR = (SERVER, Socket.UDP_PORT)

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect(TCP_ADDR)
tcp_socket = TCP_Socket(socket=tcp_sock, address=tcp_sock.getsockname())
print(tcp_sock.getsockname())

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket = UDP_Socket(socket=udp_sock, address=UDP_ADDR)

resume = True
loop = True

class Client(Socket):
    tcp_socket: TCP_Socket = None
    udp_socket: UDP_Socket = None
    lock = threading.Lock()

    def __init__(self, tcp_socket, udp_socket) -> None:
        super().__init__()
        Client.tcp_socket = tcp_socket
        Client.udp_socket = udp_socket
        self.user = None
        tcp_thread = threading.Thread(target=self.listen_tcp, daemon=True)
        tcp_thread.start()
        udp_thread = threading.Thread(target=self.send_hello, daemon=True)
        udp_thread.start()

    def listen_tcp(self):
        while True:
            try:
                packet_header, packet_data = Client.tcp_socket.receive_message()
                request = packet_data['request']
                with lock:
                    if request == 'LOGIN' or request == 'REGISTER':
                        if packet_header == 'OK':
                            user = packet_data['user']
                            self.user = user
                        message = packet_data['msg']
                        print(message)
                    elif request == 'LOGOUT':
                        if packet_header == 'OK':
                            self.user = None
                        message = packet_data['msg']
                        print(message)
                    elif request == 'SEARCH':
                        if packet_header == 'OK':
                            user_address = packet_data['address']
                            print(user_address)
                            
                        message = packet_data['msg']
                        print(message)
                    else:
                        pass
                global resume
                resume = True
            except ConnectionResetError as e:
                print('\nConnection to server is closed forcely')
                global loop
                loop = False
                sys.exit()

            except Exception as e:
                print(e.__class__)

    def listen_udp(self):
        while True:
            try:
                packet_header, packet_data = Client.udp_socket.receive_message()
            except:
                pass

    def send_tcp(self, header, message):
        self.tcp_socket.send(header, message)

    def send_hello(self):
        while True:
            if self.user is not None:
                obj = {'username': self.user.username}
                self.udp_socket.send('HELLO', obj)
                time.sleep(60)

    def make_request(self, header):
        if header == 'REGISTER' or header == 'LOGIN':
            username = input('>username: ')
            password = input('>password: ')
            obj = {'username': username, 'password': password}
            self.send_tcp(header, obj)
        elif header == 'LOGOUT':
            self.send_tcp('LOGOUT', self.user)
        elif header == 'SEARCH':
            username = input('>username: ')
            obj = {'username': username}
            self.send_tcp('SEARCH', obj)
        else:
            pass


def main():
    client = Client(tcp_socket=tcp_socket, udp_socket=udp_socket)
    global resume
    while loop:
        if resume:
            header = input(
                '>Type operation that you want to make: ').upper()
            if header not in Socket.REQUEST_HEADERS:
                print('Invalid operation')
                continue
            else:
                resume = False
                client.make_request(header)

    sys.exit()

if __name__ == '__main__':
    main()
