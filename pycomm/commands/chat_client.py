#!/usr/bin/env python3

import socket
import sys
import errno

from prompt_toolkit.shortcuts import prompt

from pycomm.commands.prompt_styles import message_style


class ChatClient:

    def __init__(self, conn_ip, port, username):
        self.ENCODING = 'utf-8'
        self.HEADER_LENGTH = 10

        self.host = conn_ip
        self.port = port
        self.user = username
        self.client_socket = None

    # def _receive_message(self, client_socket):
    #     """Handles the reception of messages"""
    #     try:
    #         # Receive the message header
    #         message_header = client_socket.recv(self.HEADER_LENGTH)
    #
    #         # If no data was received then the client gracefully exited
    #         if not len(message_header):
    #             return False
    #
    #         # Calculate the message length
    #         message_length = int(message_header.decode(self.ENCODING).strip())
    #
    #         # Return a dictionary containing the message header and message data
    #         return {'header': message_header,
    #                 'data': client_socket.recv(message_length)}
    #
    #     except:
    #         # Client closed the connection in an unnatural manner
    #         return

    def connect(self):
        # Configure client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.client_socket.setblocking(False)

        username = self.user.encode(self.ENCODING)
        # Form the username data and send it to the server
        username_header = f"{len(username): <{self.HEADER_LENGTH}}".encode(self.ENCODING)
        self.client_socket.send(username_header + username)

        # Start main client loop
        while True:
            message = prompt(self.user + '> ', style=message_style)

            if message:
                # Prepare the message with a header
                message = message.encode(self.ENCODING)
                message_header = f"{len(message): <{self.HEADER_LENGTH}}".encode(self.ENCODING)

                # Send the message to the server
                self.client_socket.send(message_header + message)

            try:

                # Loop over received messages
                while True:

                    # Receive the header of the username
                    username_header = self.client_socket.recv(self.HEADER_LENGTH)

                    # If no data is received the the server closed the connection gracefully
                    if not username_header:
                        print('Connection closed by the server')
                        sys.exit()

                    # Receive and decode the username
                    username_length = int(username_header.decode(self.ENCODING).strip())
                    username = self.client_socket.recv(username_length).decode(self.ENCODING)

                    # Now do the same for the message
                    message_header = self.client_socket.recv(self.HEADER_LENGTH)
                    message_length = int(message_header.decode(self.ENCODING).strip())
                    message = self.client_socket.recv(message_length).decode(self.ENCODING)

                    # Print the message
                    print(f"{username} > {message}")
            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()

                # Nothing was received
                continue

            except Exception as e:
                # Any other exception - something happened, exit
                print('Reading error: '.format(str(e)))
                sys.exit()
