from common.protocol import Protocol
from util import *
import socket
import pickle
import logging
import inspect

logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s — %(levelname)s — %(CALLER)s — %(message)s',
                    filemode='w')
logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)

class UDP_Socket(Protocol):
    def __init__(self, socket: socket.socket, address):
        super().__init__()
        self.socket = socket
        self.address = address

    def create_message(self, header, message):
        message = pickle.dumps(message)
        message = bytes(f'{header:<{Protocol.HEADER_LENGTH}}', Protocol.FORMAT) + bytes(f'{len(message):<{Protocol.HEADER_LENGTH}}',
                                                                                    Protocol.FORMAT) + message
        message = message + \
            bytes(f'{len(message):<{Protocol.UDP_PACKET_SIZE - len(message)}}', Protocol.FORMAT)
        return bytes(message)

    def receive_message(self):
        packet = self.socket.recv(Protocol.UDP_PACKET_SIZE)
        packet_header = packet[:Protocol.HEADER_LENGTH].decode('utf-8').rstrip(' ')
        if (packet_header not in Protocol.RESPONSE_HEADERS and packet_header not in Protocol.REQUEST_HEADERS):
            message = self.create_message(
                'INVALID', 'Invalid header. Closing connection!')
            self.socket.sendto(message, self.address)
            self.socket.close()

        packet_length = int(
            packet[Protocol.HEADER_LENGTH: 2 * Protocol.HEADER_LENGTH].decode('utf-8').strip())
        packet_data = packet[2 * Protocol.HEADER_LENGTH: 2 *
                             Protocol.HEADER_LENGTH + packet_length]
        packet_data = pickle.loads(packet_data)

        return packet_header, packet_data

    def send(self, header, message, logmessage):
        message = self.create_message(header, message)
        caller_method = inspect.currentframe().f_back.f_code.co_name
        caller_class = inspect.currentframe().f_back.f_locals["self"].__class__.__name__
        caller = f'{caller_class}->{caller_method}'
        logger.info(logmessage, extra={'CALLER' : caller})
        self.socket.sendto(message, self.address)
