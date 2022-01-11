import errno
import time
import socket
import threading
import sys
from common.tcp_socket import TCP_Socket
from common.udp_socket import UDP_Socket
from common.our_sock import Socket
from common.util import *

port_list = range(5000, 6000, 42)

lock = threading.Lock()
# getting local ip automatically
SERVER = socket.gethostbyname('localhost')
IP = socket.gethostbyname('localhost')
TCP_ADDR = (SERVER, Socket.TCP_PORT)
UDP_ADDR = (SERVER, Socket.UDP_PORT)

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect(TCP_ADDR)

chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
chat_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

multiple_chat = False
loop = True

for port in port_list:
    try:
        chat_sock.bind((IP, port))
        print(f'Client is listening on {(IP,port)}')
        break
    except:
        print(f'port {port} is unavaliable trying another port')

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tcp_socket = TCP_Socket(socket=tcp_sock, address=tcp_sock.getsockname())
udp_socket = UDP_Socket(socket=udp_sock, address=UDP_ADDR)
chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())

resume = True
loop = True
chat = False


class Peer(Socket):

    def __init__(self, tcp_socket, udp_socket, peer_server):
        """
        Threads are created to send/receive tcp and udp messages sent from the registry
        Args:
            tcp_socket ([TCP_Socket])
            udp_socket ([UDP_Socket])
            client_chat ([PeerServer])
        """

        super().__init__()
        self.tcp_socket: TCP_Socket = tcp_socket
        self.udp_socket: UDP_Socket = udp_socket
        self.user = None
        self.peer_server: PeerServer = peer_server
        

        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()
        udp_thread = threading.Thread(target=self.send_hello)
        udp_thread.start()

    def listen_tcp(self):
        global resume
        while True:
            try:
                packet_header, packet_data = self.tcp_socket.receive_message()
                with lock:
                    request = packet_data['request']
                    if request == 'LOGIN' or request == 'REGISTER':
                        if packet_header == 'OK':
                            user = packet_data['user']
                            self.user = user
                            self.peer_server.user = user
                        message = packet_data['msg']
                        print(message)
                        resume = True
                    elif request == 'LOGOUT':
                        if packet_header == 'OK':
                            self.user = None
                        message = packet_data['msg']
                        print(message)
                        resume = True
                    elif request == 'SEARCH':
                        if packet_header == 'OK':
                            user_address = packet_data['address']
                            print(user_address)
                        message = packet_data['msg']
                        print(message)
                        resume = True
                    elif request == 'CHATREQUESTREG':
                        if packet_header == 'OK':
                            user_address = packet_data['address']
                            self.peer_server.peer_address = user_address
                            self.peer_server.send_chat_request()
                             
                        else:
                            message = packet_data['msg']
                            resume = True   
                            print(message)
                    elif  request == 'MULTICHATREQUESTREG':               
                        if packet_header == 'MULTIOK':
                            self.user.busy = True
                            online_users_list = packet_data['list']
                            self.peer_server.create_multiple_rchat_requests_threads(online_users_list)     
                        
                        else:
                            message = packet_data['msg']
                            resume = True   
                            print(message)   
                    else:
                        pass                
                        
            except OSError as e:
                print('\nConnection to server is closed forcely')
                global loop
                with lock:
                    loop = False
                sys.exit()

            except Exception as e:
                with lock:
                    resume = True
                print(e)

    def listen_udp(self):
        while True:
            try:
                self.udp_socket.receive_message()
            except:
                pass

    def send_hello(self):
        while True:
            if self.user is not None:
                obj = {'username': self.user.username}
                self.udp_socket.send('HELLO', obj)
                time.sleep(60)

    def make_request(self, header):
        global resume
        resume = False
        global multiple_chat
        if header == 'REGISTER' or header == 'LOGIN':
            username = input('> username: ')
            password = input('> password: ')
            obj = {'username': username, 'password': password, 'chatport': port}
            if not self.user:
                self.tcp_socket.send(header, obj)
            else:
                print('You are currently logged in')
                resume = True
        elif header == 'LOGOUT':
            self.tcp_socket.send('LOGOUT', self.user)
        elif header == 'SEARCH':
            username = input('> username: ')
            obj = {'username': username}
            self.tcp_socket.send('SEARCH', obj)
        elif header == 'CHATREQUEST':
            usernames = input(
                '> Enter the username of the user you want to chat: ')
            username_list = usernames.split()    
            if len(username_list) == 1:
                obj = {'username': usernames}
                self.tcp_socket.send('CHATREQUESTREG', obj)
            elif len(username_list) > 1:
                multiple_chat = True
                obj = {'usernames': username_list}
                self.tcp_socket.send('MULTICHATREQUESTREG', obj)

        else:
            pass


class PeerServer(Socket):
    def __init__(self, chat_socket):
        self.tcp_socket: TCP_Socket = chat_socket
        tcp_thread = threading.Thread(target=self.listen_tcp)
        tcp_thread.start()
        self.peer_names = []
        self.chat_sockets = {}
        self.current_peers_information = []
        self.multiple_chat_peers = []
        self.owner_username = ""
        self.owner_peer_socket = None


    def chat(self):
        global chat
        global resume
        while chat:
            message = input('> ')
            if message == 'exit':
                with lock:
                    chat = False
                    resume = True
                obj = {'msg' : f'{self.user.username} is closed connection'}
                self.chat_socket.send('REJECT', obj)
                self.chat_socket = None
                self.user.busy = False
                break
            obj = {'msg': message}
            if self.chat_socket:
                self.chat_socket.send('CHAT', obj)

    def multi_chat(self):
        global multiple_chat
        global resume
        
        while multiple_chat:
            message = input('> ')
            with lock:
                for peer_username, peer_socket in self.chat_sockets.items():
                    if peer_socket == None:
                        continue
                    if message == 'exit':
                        obj = {'msg' : f'{self.user.username} is closed connection'}
                        self.chat_sockets = {}
                        self.user.busy = False
                        resume = True
                        peer_socket.send('MULTIREJECT', obj)
                        break
                    else:
                        obj = {'msg': self.user.username+message}
                        peer_socket.send('MULTICHAT', obj)




    def send_chat_request(self):
        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_sock.connect(self.peer_address)
        self.chat_socket = TCP_Socket(
            socket=chat_sock, address=chat_sock.getsockname())
        obj = {'username': self.user.username, 'request': 'CHATREQUEST', 'address' : self.tcp_socket.socket.getsockname()}
        self.chat_socket.send('CHATREQUEST', obj)

    def create_multiple_rchat_requests_threads(self, ls):
        for obj in ls:
            address = obj['chat_address']
            ar = {'info':self.current_peers_information,'peer_address':address,'peer_username':obj['username'],'username': self.user.username, 'request': 'MULTICHATREQUEST', 'address' : ''}  
            self.send_multiple_chat_requests(ar)
    

    def send_multiple_chat_requests(self, ar):
        address = ar['peer_address']
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.connect(address)
        temp_socket = TCP_Socket(
                socket=temp_sock, address=temp_sock.getsockname())
        ar['address'] = self.tcp_socket.socket.getsockname()       
        temp_socket.send('MULTICHATREQUEST', ar)

    def send_new_peer_inf_to_all_peers(self,new_peer):
        with lock:
            for peer in self.current_peers_information:
                temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_sock.connect(peer['peer_address'])
                temp_socket = TCP_Socket(socket=temp_sock, address=temp_sock.getsockname())
                temp_socket.send('NEWPEER',new_peer)

    def receive_packet(self, client_socket: TCP_Socket):
        global resume
        resume = False
        global chat
        global multiple_chat
        while   loop:
            try:
                packet_header, packet_data = client_socket.receive_message()
                with lock:
                    if packet_header == 'NEWPEER':
                        new_peer = packet_data['new_peer']
                        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        temp_sock.connect(new_peer['peer_address'])
                        temp_socket = TCP_Socket(socket=temp_sock, address=temp_sock.getsockname())
                        self.chat_sockets['peer_username'] = temp_socket

                    if packet_header == 'CHATREQUEST':
                        chat_socket_address = packet_data['address']
                        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        chat_sock.connect(chat_socket_address)
                        self.chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())
                        if self.user.busy:
                            obj = {
                                'msg': 'User is currently chatting with another person'}
                            resume = True
                            self.chat_socket.send('BUSY', obj)
                        else:
                            username = packet_data['username']
                            print(f'\nUser {username} wants to chat with you [Y/N]:', end=' ')
                            accept = input().lower()
                            while accept != 'y' and accept != 'n': 
                                accept = input('Invalid option enter [Y/N]: ').lower()

                            accept = True if accept == 'y' else False
                            if accept:
                                self.user.busy = True
                                self.user.peer_name = username
                                obj = {
                                    'msg': f'{self.user.username} accepted to chat', 'username' : self.user.username}
                                chat = True
                                self.chat_socket.send('OK', obj)
                         

                            else:
                                obj = {
                                    'msg': f'{self.user.username} rejected to chat'}
                                resume = True
                                self.chat_socket.send('REJECT', obj)
                    if packet_header == 'MULTICHATREQUEST':
                        owner_username = packet_data['username']
                        chat_socket_address = packet_data['address']
                        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        chat_sock.connect(chat_socket_address)
                        self.chat_socket = TCP_Socket(socket=chat_sock, address=chat_sock.getsockname())
                      
                        if self.user.busy:
                                obj = {
                                    'msg': 'User is currently chatting with another person','peer_username':packet_data['peer_username']}
                                resume = True
                                multiple_chat = False
                                self.chat_socket.send('MULTIBUSY', obj)

                        else:
                                #ar = {'info':self.current_peers_information,'peer_address':address,'peer_username':obj['username'],'username': self.user.username, 'request': 'MULTICHATREQUEST', 'address' : ''}
              
                            print(f'\nUser {owner_username} invites you to multiple chat with all listed users [Y/N]: ', end=' ')
                            accept = input().lower()
                            while accept != 'y' and accept != 'n': 
                                accept = input('Invalid option enter [Y/N]: ').lower()

                            accept = True if accept == 'y' else False
                            if accept:
                                new_peer = {'peer_username':packet_data['peer_username'], 'peer_address':packet_data['peer_address']}
                                obj = {
                                'msg': f'{self.user.username} accepted to chat', 'new_peer' : new_peer}
                                self.chat_socket.send('MULTIOK', obj)
                                temp = self.chat_socket
                                self.chat_sockets[owner_username] = temp
                                
                                for info in packet_data['info']:
                                    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    temp_sock.connect(info['peer_address'])
                                    temp_socket = TCP_Socket(socket=temp_sock, address=temp_sock.getsockname())
                                    self.chat_sockets[info['peer_username']] = temp_socket
                                chat = True
                                multiple_chat = True
                                
                            else:
                                obj = {
                                    'msg': f'{self.user.username} rejected to chat','peer_username':packet_data['peer_username']}
                                resume = True
                                multiple_chat = False
                                self.chat_socket.send('MULTIREJECT', obj)

                                       

                    elif packet_header in Socket.RESPONSE_HEADERS:
                        message = packet_data['msg']
                        if packet_header == 'OK':
                            self.user.busy = True
                            self.user.peer_name = packet_data['username']
                            chat = True 
                        #changed
                        if packet_header == 'MULTIOK':
                            self.user.busy = True

                            # send new peer to all peers
                            new_peer_temp = packet_data['new_peer']
                            self.send_new_peer_inf_to_all_peers(new_peer_temp)
                            self.current_peers_information.append(new_peer_temp)
                                                    
                            temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            temp_sock.connect(new_peer_temp['peer_address'])
                            temp_socket = TCP_Socket(socket=temp_sock, address=temp_sock.getsockname())
                            self.chat_sockets[new_peer_temp['peer_username']] = temp_socket
                            multichat = True     
                        if packet_header == 'MULTIREJECT' or packet_header == 'MULTIBUSY':

                            self.chat_sockets[packet_data['peer_username']] = None
                            
     

                    elif packet_header == 'CHAT':
                        message = packet_data['msg']
                        print(f'{self.user.peer_name}: {message}')
                        print('> ', end='')
                        sys.stdout.flush()
                    elif packet_header == 'MULTICHAT':
                        message = packet_data['msg']
                        print(f'{message}')
                        print('> ', end='')
                        sys.stdout.flush()

            except IOError as e:
                if e.errno == errno.EBADF:
                    with lock:
                        print('Client socket is closed')
                        resume = True
                        chat = False
                        sys.exit()


            except Exception as e:
                print(e)
                pass

    def listen_tcp(self):
        self.tcp_socket.socket.listen()
        while True:
            client_socket, client_address = self.tcp_socket.socket.accept()
            client_socket = TCP_Socket(
                socket=client_socket, address=client_address)
            client_thread = threading.Thread(target=self.receive_packet, args=(client_socket, ))
            client_thread.start()
    


def main():
    global resume
    peer_server = PeerServer(chat_socket=chat_socket)
    peer = Peer(tcp_socket=tcp_socket,
                    udp_socket=udp_socket, peer_server=peer_server)

    while loop:
        if resume:
            header = input(
                '> Type operation that you want to make: ').upper()
            if header not in Socket.REQUEST_HEADERS:
                print('Invalid operation')
                continue
            else:
                peer.make_request(header)
        elif chat and multiple_chat:
            peer.peer_server.multi_chat()        
        elif chat:
            peer.peer_server.chat()


    sys.exit()


if __name__ == '__main__':
    main()
