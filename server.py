from datetime import datetime
import socket
import sys
import threading
import pickle
from udp_socket import UDP_Socket
from util import *
from user import User
lock = threading.Lock()

UDP_PACKET_SIZE = 1024
HEADER_LENGTH = 16
HEADERS = ['REGISTER', 'LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'OK', 'REJECT',
           'BUSY']  # We can use this by enumerating
IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 2424
UDP_PORT = 4242

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

tcp_sock.bind((IP, TCP_PORT))

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((IP, UDP_PORT))

clients = []


def register(packet_data, client_socket, client_address):
    username = packet_data['username']
    password = packet_data['password']

    with lock:
        if not check_user(clients, username):
            user = User(username, password, client_address, datetime.now(),status=True)
            clients.append(user)
            client_socket.send(b'The registration is complete.')
        else:
            client_socket.send(b'This username is already used.')


def login(packet_data, client_socket, client_address):
    username = packet_data['username']
    password = packet_data['password']
    with lock:
        user = check_user(clients, username)
        if (user is not None) and (check_password(user, password)):
            user.status = True
            user.last_active = datetime.now()
            client_socket.send(b'Connected to chatroom')
        elif user is None:
            client_socket.send(b'Invalid username. Please register first')
        else:
            client_socket.send(b'Invalid password. Please try again')


def logout(packet_data, client_socket, client_address):
    user = check_user_by_client_address(clients, client_address)
    with lock:
        if user is not None:
            user.status = False
            client_socket.send(b'Logout')


def receive_packet_tcp(client_socket, client_address):
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
                client_socket.close()

            packet_length = client_socket.recv(HEADER_LENGTH)
            packet_length = int(packet_length.decode('utf-8').strip())
            packet_data = client_socket.recv(packet_length)
            packet_data = pickle.loads(packet_data)
            if packet_header == 'REGISTER':
                register(packet_data, client_socket, client_address)
            elif packet_header == 'LOGIN':
                login(packet_data, client_socket, client_address)
            elif packet_header == 'LOGOUT' and check_user_by_client_address(clients, client_address):
                logout(packet_data, client_socket, client_address)
            else:
                pass

        except Exception as e:
            print(e)


# listen on the tcp socket
def listen_tcp():
    tcp_sock.listen()
    print(f"[LISTENING] Server is listening on {IP, TCP_PORT}")
    while True:
        client_socket, client_address = tcp_sock.accept()
        receive_packet_tcp(client_socket, client_address)


def receive_packet_udp(client_socket):
    packet = client_socket.recv(UDP_PACKET_SIZE)
    packet_header = packet[:HEADER_LENGTH].decode('utf-8').rstrip(' ')
    if packet_header not in HEADERS:
        client_socket.send(b'Invalid header. Closing connection!')
        client_socket.close()

    packet_length = int(packet[HEADER_LENGTH: 2* HEADER_LENGTH].decode('utf-8').strip())
    packet_data = packet[2*HEADER_LENGTH: 2*HEADER_LENGTH + packet_length]
    packet_data = pickle.loads(packet_data)

    return packet_header, packet_data


def active(user : User):
    while True:
        now = datetime.now()
        delta = (now - user.last_active).total_seconds()
        if delta > 40:
            with lock:
                user.status = False
                sys.exit()

# listen on a udp socket
def listen_udp():
    udp_socket = UDP_Socket(clients, udp_sock)
    while True:
        packet_header, packet_data = receive_packet_udp(udp_socket.socket)
        username = packet_data['username']
        user: User = check_user(udp_socket.clients, username)
        make_thread = user is not None
        # TODO Give created threads name and if it doesnt exist create new if it exist connect to it
        # If this is not done for each HELLO message sent by the same user a new thread will be created
        if make_thread:
            user_thread = threading.Thread(target=active, args=(user,))
            user_thread.start()
            make_thread = False

        if user and packet_header == 'HELLO':
            user.last_active = datetime.now()
            print('yarraaaa bere ')


tcp_listener = threading.Thread(target=listen_tcp)
tcp_listener.start()

udp_listener = threading.Thread(target=listen_udp)
udp_listener.start()
