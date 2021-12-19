import socket
import threading
from util import *
from user import User

HEADER_LENGTH  = 10
IP = '127.0.0.1'
TCP_PORT = 2424
UDP_PORT = 4242

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.bind((IP, TCP_PORT))

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((IP, UDP_PORT))

clients = []

"""
HEADERS:
    LOGIN
    LOGOUT
    HELLO
    CHATREQUEST
    OK
    REJECT
    BUSY
"""

def receive_packet(client_socket : socket.socket):
    """
    Receive a packet from a client socket
    Args:
     - client_socket: socket.socket
    
    Return:
     - Contents of the packet
     - False
    
    """
    try:
        packet_header = client_socket.recv(HEADER_LENGTH)
        if not len(packet_header):
            return False

        packet_length = int(packet_header.decode('utf-8').strip())
        packet_data = client_socket.recv(packet_length)
        return packet_header , packet_data
    except:
        return False


def listen_tcp():
    tcp_socket = TCP_Socket(clients, tcp_sock)
    while True:
        client_socket, client_address = tcp_socket.socket.accept()
        packet_header, packet_data = receive_packet(client_socket)
        
    pass


def listen_udp():
    pass



tcp_listener = threading.Thread(target=listen_tcp)
tcp_listener.start()

udp_listener = threading.Thread(target=listen_udp)
udp_listener.start()


class TCP_Socket:
    def __init__(self, clients, socket):
        self.clients = clients
        self.socket = socket
        pass

    def login(self):
        pass

    def register(self):
        pass

    def logout(self):
        pass
    

class UDP_Socket:
    def __init__(self, clients):
        pass

    def __call__(self):
        pass
