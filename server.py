import socket
import threading
from tcp_socket import TCP_Socket
from udp_socket import UDP_Socket
from util import *
from user import User

HEADER_LENGTH = 16
HEADERS = ['LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'OK', 'REJECT', 'BUSY'] # We can use this by enumerating 
IP = '127.0.0.1'
TCP_PORT = 2424
UDP_PORT = 4242

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.bind((IP, TCP_PORT))

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((IP, UDP_PORT))

clients = []


def receive_packet(client_socket: socket.socket):
    """
    Receive a packet from a client socket. Return header and data of the packet
    Args:
     - client_socket: socket.socket

    Return:
     - Packet Header
     - Packet data
    """
    try:
        # First Header length part of package contains the header and the second part contains the packet length
        packet_header = client_socket.recv(HEADER_LENGTH)
        if packet_header not in HEADERS:
            client_socket.send(b'Invalid header. Closing connection!')
            client_socket.close()
        
        packet_length = client_socket.recv(HEADER_LENGTH)
        packet_length = int(packet_length.decode('utf-8').strip())
        packet_data = client_socket.recv(packet_length)
        return packet_header.decode('utf-8'), packet_data
    except:
        return False


# listen on the tcp socket
def listen_tcp():
    tcp_socket = TCP_Socket(clients, tcp_sock)
    while True:
        client_socket, client_address = tcp_socket.socket.accept()
        packet_header, packet_data = receive_packet(client_socket)


        # This is a risky implementation because idk what will happen when more than one client sends packets at the same time.
        # This is done because i didn't want to use switch case to call methods for headers
        tcp_socket.client_address = client_address
        tcp_socket.client_socket = client_socket
        tcp_socket.packet_data = packet_data

        header_method = getattr(tcp_socket, packet_header.lower())
        result = header_method()


# listen on a udp socket
def listen_udp():
    udp_socket = UDP_Socket(clients, udp_sock)
    while True:
        data, client_address = udp_socket.socket.recvfrom(HEADER_LENGTH)
        header = data.decode('utf-8')

        header_method = getattr(udp_socket, header.lower())
        user : User = check_user_fromip(udp_socket.clients, client_address)
        active_thread = threading.Thread(target=user.active)
        active_thread.start()

        
tcp_listener = threading.Thread(target=listen_tcp)
tcp_listener.start()

udp_listener = threading.Thread(target=listen_udp)
udp_listener.start()

