from datetime import datetime
import socket
import sys
import threading
import pickle
from udp_socket import UDP_Socket
from util import *
from user import User
import errno

lock = threading.Lock()

UDP_PACKET_SIZE = 1024
HEADER_LENGTH = 16
HEADERS = ['REGISTER', 'LOGIN', 'LOGOUT', 'HELLO', 'CHATREQUEST', 'OK', 'REJECT',
           'BUSY', 'SEARCH']  # We can use this by enumerating
IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 2424
UDP_PORT = 4242

FORMAT = 'utf-8'

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_sock.bind((IP, TCP_PORT))

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind((IP, UDP_PORT))

clients = []


def register(packet_data, client_socket, client_address):
    """
    register a user with the server
    Args:
     - packet_data, client_socket, client_address
     - packet_data, client_socket, client_address):username=packet_data['username']password=packet_data['password']withlock:ifnotcheck_user(clients, username
    
    """
    username = packet_data['username']
    password = packet_data['password']

    with lock:
        if not check_user(clients, username):
            user = User(username, password, client_address, datetime.now(), status=True)
            clients.append(user)
            client_socket.send(b'The registration is complete.')
        else:
            client_socket.send(b'This username is already used.')


def login(packet_data, client_socket):
    """
    login to chatroom
    Args:
     - packet_data, client_socket
    
    """
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


def logout(client_socket, client_address):
    """
    send a logout packet to the client
    Args:
     -  client_socket, client_address

    """
    user = check_user_by_client_address(clients, client_address)
    with lock:
        if user is not None:
            user.status = False
            client_socket.send(b'Logout')


def search(packet_data, client_socket):
    """
     send the address of  requested client to the client
     Args:
      - packet_data, client_socket

     """

    searched_username = packet_data['searched_username']
    user = check_user(clients, searched_username)
    with lock:
        if user is not None:
            msg = str(user.client_address[0]) + ',' + str(+user.client_address[1])
            client_socket.send(bytes(msg, FORMAT))
        else:
            client_socket.send(b'NOT FOUND')


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

            user = check_user_by_client_address(clients, client_address)
            if packet_header == 'REGISTER':
                register(packet_data, client_socket, client_address)
            elif packet_header == 'LOGIN':
                login(packet_data, client_socket)
            elif packet_header == 'LOGOUT' and user:
                logout(client_socket, client_address)

            elif packet_header == 'SEARCH':
                search(packet_data, client_socket)
            else:
                pass

        except IOError as e:
            if e.errno == errno.EBADF:
                print('Client socket is closed')
                sys.exit()


# listen for incoming tcp packets on the socket
def listen_tcp():
    tcp_sock.listen()
    print(f"[LISTENING] Server is listening on {IP, TCP_PORT}")
    while True:
        client_socket, client_address = tcp_sock.accept()
        # Create new thread for every incoming tcp connection 
        client_thread = threading.Thread(target=receive_packet_tcp, args=(client_socket, client_address))
        client_thread.start()


def receive_packet_udp(udp_socket):
    """
    receive a packet from a udp socket
    Args:
     - udp_socket
    
    Return:
     - packet_header,packet_data
    
    """
    packet = udp_socket.recv(UDP_PACKET_SIZE)
    packet_header = packet[:HEADER_LENGTH].decode('utf-8').rstrip(' ')
    if packet_header not in HEADERS:
        udp_socket.send(b'Invalid header. Closing connection!')
        udp_socket.close()

    packet_length = int(packet[HEADER_LENGTH: 2 * HEADER_LENGTH].decode('utf-8').strip())
    packet_data = packet[2 * HEADER_LENGTH: 2 * HEADER_LENGTH + packet_length]
    packet_data = pickle.loads(packet_data)

    return packet_header, packet_data


def active(user: User):
    """
    Check if the user is not active for more than 200 seconds
    Args:
     - user:User
    
    """
    while True:
        now = datetime.now()
        delta = (now - user.last_active).total_seconds()
        if delta > 200:
            with lock:
                user.status = False
                sys.exit()


# listen for packets on a udp socket
def listen_udp():
    udp_socket = UDP_Socket(clients, udp_sock)
    while True:
        packet_header, packet_data = receive_packet_udp(udp_socket.socket)
        username = packet_data['username']
        user: User = check_user(udp_socket.clients, username)
        make_thread = user is not None
        # if user doesnt have a thread that is already created make a thread for that user 
        if make_thread and not user.thread_active:
            user_thread = threading.Thread(target=active, args=(user,))
            user_thread.start()
            make_thread = False
            user.thread_active = True
        # in each HELLO message reset the timer
        if user and packet_header == 'HELLO':
            print(f'Received udp packet with the header {packet_header}')
            user.last_active = datetime.now()


tcp_listener = threading.Thread(target=listen_tcp)
tcp_listener.start()

udp_listener = threading.Thread(target=listen_udp)
udp_listener.start()
