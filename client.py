import socket
import pickle
import sys

TCP_PORT = 2424
UDP_PORT = 4242
HEADER_LENGTH = 16
FORMAT = 'utf-8'
SERVER = socket.gethostbyname(socket.gethostname())  # getting local ip automatically
TCP_ADDR = (SERVER, TCP_PORT)
UDP_ADDR = (SERVER, UDP_PORT)

tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_client.connect(TCP_ADDR)

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(msg, header_message, type='tcp', udp_addr=None):
    # message = msg.encode(FORMAT)
    message = pickle.dumps(msg)
    message = bytes(f'{header_message:<{HEADER_LENGTH}}', FORMAT) + bytes(f'{len(message):<{HEADER_LENGTH}}',
                                                                          FORMAT) + message
    if type == 'tcp':
        tcp_client.send(bytes(message))
    elif type == 'udp':
        udp_client.sendto(bytes(message), udp_addr)
    else:
        print('Unknown argument')
        sys.exit()
    print(tcp_client.recv(2048).decode(FORMAT))


dictionary = {'username': 'zeynep', 'password': '123'}
send(dictionary, 'REGISTER')

send(dictionary, 'LOGOUT')

dictionary = {'username': 'zeynep', 'password': '12'}
send(dictionary, 'LOGIN')

dictionary = {'username': 'zeynep', 'password': '123'}
send(dictionary, 'LOGIN')

dictionary = {'username': 'zeynep'}
send(dictionary, 'HELLO', type='udp', udp_addr=UDP_ADDR)

dictionary = {'username': 'zeynep'}
send(dictionary, 'HELLO', type='udp', udp_addr=UDP_ADDR)

while True:
    tcp_client.recv(2048).decode(FORMAT)