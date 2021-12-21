import socket
import threading
import pickle
from tcp_socket import TCP_Socket
from udp_socket import UDP_Socket
from util import *
from user import User

HEADER_LENGTH = 16
HEADERS = ['REGISTER', 'LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'OK', 'REJECT',
           'BUSY']  # We can use this by enumerating
IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 2425
UDP_PORT = 4242

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.bind((IP, TCP_PORT))

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((IP, UDP_PORT))

clients = []


def register(packet_data, client_socket, client_address):
    username = packet_data['username']
    password = packet_data['password']

    with threading.Lock():
        if not check_user(clients, username):
            user = User(username, password, client_address, status=True)
            clients.append(user)
            client_socket.send(b'The registration is complete.')
        else:
            client_socket.send(b'This username has already used.')


def login(packet_data, client_socket,client_address):
    pass


def logout(packet_data, client_socket,client_address):
    pass


def receive_packet(client_socket, client_address):
    """
    Receive a packet from a client socket. Return header and data of the packet
    Args:
     - client_socket: socket.socket

    Return:
     - Packet Header
     - Packet data
    """
    connected = True

    while connected:
        try:
            # First Header length part of package contains the header and the second part contains the packet length
            packet_header = client_socket.recv(HEADER_LENGTH)
            packet_header = packet_header.decode('utf-8').rstrip(' ')
            if packet_header not in HEADERS:
                client_socket.send(b'Invalid header. Closing connection!')
                connected = False
                client_socket.close()

            packet_length = client_socket.recv(HEADER_LENGTH)
            packet_length = int(packet_length.decode('utf-8').strip())
            packet_data = client_socket.recv(packet_length)
            packet_data = pickle.loads(packet_data)
            print(packet_data)

            if packet_header == 'REGISTER':
                register(packet_data, client_socket, client_address)
            elif packet_header == 'LOGIN':
                login(packet_data, client_socket, client_address)
            elif packet_header == 'LOGOUT':
                logout(packet_data, client_socket, client_address)
            else:
                pass

        except:
            return False


# listen on the tcp socket
def listen_tcp():
    tcp_sock.listen()
    print(f"[LISTENING] Server is listening on {IP, TCP_PORT}")
    while True:
        client_socket, client_address = tcp_sock.accept()
        thread = threading.Thread(target=receive_packet, args=(client_socket, client_address))
        thread.start()


# listen on a udp socket
def listen_udp():
    udp_socket = UDP_Socket(clients, udp_sock)
    while True:
        data, client_address = udp_socket.socket.recvfrom(HEADER_LENGTH)
        header = data.decode('utf-8')

        header_method = getattr(udp_socket, header.lower())
        user: User = check_user_fromip(udp_socket.clients, client_address)
        active_thread = threading.Thread(target=user.active)
        active_thread.start()


tcp_listener = threading.Thread(target=listen_tcp)
tcp_listener.start()

udp_listener = threading.Thread(target=listen_udp)
udp_listener.start()
