import socket
import pickle
import threading

TCP_PORT = 2424
UDP_PORT = 4242
HEADER_LENGTH = 16
UDP_PACKET_SIZE = 1024
FORMAT = 'utf-8'
SERVER = socket.gethostbyname(socket.gethostname())  # getting local ip automatically
TCP_ADDR = (SERVER, TCP_PORT)
UDP_ADDR = (SERVER, UDP_PORT)

tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_client.connect(TCP_ADDR)

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def tcp_message(msg, header_message):
    # message = msg.encode(FORMAT)
    message = pickle.dumps(msg)
    message = bytes(f'{header_message:<{HEADER_LENGTH}}', FORMAT) + bytes(f'{len(message):<{HEADER_LENGTH}}',
                                                                          FORMAT) + message
    tcp_client.send(bytes(message))

def listen_tcp():
    while True:
        print(tcp_client.recv(2048).decode(FORMAT))


def listen_udp():
    while True:
        print(udp_client.recv(2048).decode(FORMAT))


def udp_messsage(msg, header_message, addr):
    message = pickle.dumps(msg)
    message = bytes(f'{header_message:<{HEADER_LENGTH}}', FORMAT) + bytes(f'{len(message):<{HEADER_LENGTH}}',
                                                                          FORMAT) + message
    message = message + bytes(f'{len(message):<{UDP_PACKET_SIZE}}', FORMAT)
    udp_client.sendto(bytes(message), addr)

tcp_listener = threading.Thread(target=listen_tcp)
tcp_listener.start()

udp_listener = threading.Thread(target=listen_tcp)
udp_listener.start()

dictionary = {'username': 'zeynep', 'password': '123'}
tcp_message(dictionary, 'REGISTER')

tcp_message(dictionary, 'LOGOUT')

dictionary = {'username': 'zeynep', 'password': '12'}
tcp_message(dictionary, 'LOGIN')

dictionary = {'username': 'zeynep', 'password': '123'}
tcp_message(dictionary, 'LOGIN')

dictionary = {'username': 'zeynep'}
udp_messsage(dictionary, 'HELLO', UDP_ADDR)

dictionary = {'username': 'zeynep'}
udp_messsage(dictionary, 'HELLO', UDP_ADDR)

dictionary = {'username': 'zeynep'}
udp_messsage(dictionary, 'HELLO', UDP_ADDR)