class UDP_Socket:
    """
    udp socket class
    Args:
        - self, clients, socket
    
    """
    def __init__(self, clients, socket):
        self.clients = clients
        self.socket = socket

    def hello(self):
        """
        now = datetime.date.now()
        username = self.packet_data['username'].decode('utf-8')
        user : User = check_user(clients, username)
        delta = now - user.last_active

        if delta.seconds() > 200:
            user.status = False
        """