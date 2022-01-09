import socket
import pickle
import logging
import inspect

logging.basicConfig(filename="logfile.log",
                    format='%(asctime)s — %(levelname)s — %(CALLER)s — %(message)s',
                    filemode='a')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from common.protocol import Protocol
from util import *

class TCP_Socket(Protocol):

    def __init__(self, socket: socket.socket, address):
        super().__init__()
        self.socket = socket
        self.address = address

    def create_message(self, header, message):
        message = pickle.dumps(message)
        message = bytes(f'{header:<{Protocol.HEADER_LENGTH}}', Protocol.FORMAT) + bytes(f'{len(message):<{Protocol.HEADER_LENGTH}}',
                                                                                    Protocol.FORMAT) + message
        return bytes(message)

    def receive_message(self):
        packet_header = self.socket.recv(Protocol.HEADER_LENGTH)
        packet_header = packet_header.decode('utf-8').rstrip(' ')
        if (packet_header not in Protocol.RESPONSE_HEADERS and packet_header not in Protocol.REQUEST_HEADERS):
            # We should think of a better way to include headers into messages
            message = self.create_message(
                'INVALID', 'Invalid header. Closing connection!')
            self.socket.send(message)
            self.socket.close()

        packet_length = self.socket.recv(Protocol.HEADER_LENGTH)
        packet_length = int(packet_length.decode('utf-8').strip())

        packet_data = self.socket.recv(packet_length)
        packet_data = pickle.loads(packet_data)
        return packet_header, packet_data

    def send(self, header, message, logmessage = None):
        message = self.create_message(header, message)
        if logmessage:
            caller_method = inspect.currentframe().f_back.f_code.co_name
            caller_class = inspect.currentframe().f_back.f_locals["self"].__class__.__name__
            self.log(logmessage, f'{caller_class}->{caller_method}')
        self.socket.send(message)
        
    def log(self, logmessage, caller=None):
        if caller is None:
            caller_method = inspect.currentframe().f_back.f_code.co_name
            caller_class = inspect.stack()[1][0].f_locals["self"].__class__.__name__  
            caller = f'{caller_class}->{caller_method}'
            
        logger.info(logmessage, extra={'CALLER' : caller})
        