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

