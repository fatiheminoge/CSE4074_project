from common.our_sock import Socket
from util import *
import socket
import pickle


class UDP_Socket(Socket):
    def __init__(self, socket: socket.socket, address):
        super().__init__()
        self.socket = socket
        self.address = address

    def create_message(self, header, message):
        message = pickle.dumps(message)
        message = bytes(f'{header:<{Socket.HEADER_LENGTH}}', Socket.FORMAT) + bytes(f'{len(message):<{Socket.HEADER_LENGTH}}',
                                                                                    Socket.FORMAT) + message
        message = message + \
            bytes(f'{len(message):<{Socket.UDP_PACKET_SIZE - len(message)}}', Socket.FORMAT)
        return bytes(message)

    def receive_message(self):
        packet = self.socket.recv(Socket.UDP_PACKET_SIZE)
        packet_header = packet[:Socket.HEADER_LENGTH].decode('utf-8').rstrip(' ')
        if (packet_header not in Socket.RESPONSE_HEADERS and packet_header not in Socket.REQUEST_HEADERS):
            message = self.create_message(
                'INVALID', 'Invalid header. Closing connection!')
            self.socket.sendto(message, self.address)
            self.socket.close()

        packet_length = int(
            packet[Socket.HEADER_LENGTH: 2 * Socket.HEADER_LENGTH].decode('utf-8').strip())
        packet_data = packet[2 * Socket.HEADER_LENGTH: 2 *
                             Socket.HEADER_LENGTH + packet_length]
        packet_data = pickle.loads(packet_data)

        return packet_header, packet_data

    def send(self, header, message):
        message = self.create_message(header, message)
        self.socket.sendto(message, self.address)
