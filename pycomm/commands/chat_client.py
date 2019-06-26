#!/usr/bin/env python3

import socket
import select
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

    def _receive_message(self, client_socket):
        """Handles the reception of messages"""
        try:
            # Receive the message header
            message_header = client_socket.recv(self.HEADER_LENGTH)

            # If no data was received then the client gracefully exited
            if not len(message_header):
                return False

            # Calculate the message length
            message_length = int(message_header.decode(self.ENCODING).strip())

            # Return a dictionary containing the message header and message data
            return {'header': message_header,
                    'data': client_socket.recv(message_length)}

        except:
            # Client closed the connection in an unnatural manner
            return

    def connect(self):

        # Configure client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        username = self.user.encode(self.ENCODING)
        # Form the username data and send it to the server
        username_header = f"{len(username): <{self.HEADER_LENGTH}}".encode(self.ENCODING)
        self.client_socket.send(username_header + username)


        # Start main client loop
        while True:

            read_sockets, _, _ = select.select([self.client_socket], [], [])

            for notified_socket in read_sockets:
                if notified_socket is self.client_socket:
                    received_message = self._receive_message(notified_socket)
                    print(received_message)

            message = prompt(self.user + '> ', style=message_style)

