import socket
import pickle

TCP_PORT = 2425
UDP_PORT = 4242
HEADER_LENGTH = 16
FORMAT = 'utf-8'
SERVER = socket.gethostbyname(socket.gethostname())  # getting local ip automatically
ADDR = (SERVER, TCP_PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def send(msg, header_message):
    # message = msg.encode(FORMAT)
    message = pickle.dumps(msg)
    message = bytes(f'{header_message:<{HEADER_LENGTH}}', FORMAT) + bytes(f'{len(message):<{HEADER_LENGTH}}',
                                                                          FORMAT) + message

    client.send(bytes(message))
    print(client.recv(2048).decode(FORMAT))


dictionary = {'username': 'zeynep', 'password': '123'}
send(dictionary, 'REGISTER')

send(dictionary, 'LOGOUT')

dictionary = {'username': 'zeynep', 'password': '12'}
send(dictionary, 'LOGIN')

dictionary = {'username': 'zeynep', 'password': '123'}
send(dictionary, 'LOGIN')