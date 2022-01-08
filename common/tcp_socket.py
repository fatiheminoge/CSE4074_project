from common.our_sock import Socket
from util import *
import socket
import pickle


class TCP_Socket(Socket):

    def __init__(self, socket: socket.socket, address):
        super().__init__()
        self.socket = socket
        self.address = address

    def create_message(self, header, message):
        message = pickle.dumps(message)
        message = bytes(f'{header:<{Socket.HEADER_LENGTH}}', Socket.FORMAT) + bytes(f'{len(message):<{Socket.HEADER_LENGTH}}',
                                                                                    Socket.FORMAT) + message
        return bytes(message)

    def receive_message(self):
        packet_header = self.socket.recv(Socket.HEADER_LENGTH)
        packet_header = packet_header.decode('utf-8').rstrip(' ')
        if (packet_header not in Socket.RESPONSE_HEADERS and packet_header not in Socket.REQUEST_HEADERS):
            # We should think of a better way to include headers into messages
            message = self.create_message(
                'INVALID', 'Invalid header. Closing connection!')
            self.socket.send(message)
            self.socket.close()

        packet_length = self.socket.recv(Socket.HEADER_LENGTH)
        packet_length = int(packet_length.decode('utf-8').strip())

        packet_data = self.socket.recv(packet_length)
        packet_data = pickle.loads(packet_data)
        return packet_header, packet_data

    def send(self, header, message):
        message = self.create_message(header, message)
        self.socket.send(message)
