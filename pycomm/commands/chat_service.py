# chat_service.py - Object representing a chat server
import socket
import select


class ChatService:

    def __init__(self, host, port):
        self.ENCODING = 'utf-8'
        self.HEADER_LENGTH = 10

        self.host = host
        self.port = port

        # Dictionary of client data
        self.clients = {}

        # Configure the server socket
        self.server_socket = None
        self.sockets_list = []

    def send_error(self, client_socket, message):
        # Return an error message to the client
        message_header = f"{len(message): <{self.HEADER_LENGTH}}".encode(self.ENCODING)
        message = message.encode(self.ENCODING)
        client_socket.send(message_header + message)

    def _broadcast(self, user, msg, conn):
        """Broadcasts messages to clients connected to the service"""
        for client in self.clients:

            # Don't send to the src client
            if client != conn:
                # Send the user header and data
                # along with the message header and data
                client.send(user['header'] + user['data']
                            + msg['header'] + msg['data'])

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
            return False

    def _purge_connections(self):
        """Purges all existing connections"""
        for conn in self.sockets_list:
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except socket.error:
                print("[-] A connection was already closed")

        del self.sockets_list[:]

    def start(self):
        """Enables the service"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.setblocking(False)
        self.server_socket.listen(10)

        self.sockets_list = [self.server_socket]

        print(f'Listening for connections on {self.host}:{self.port}...')

        # Start the main server loop
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [],
                                                               self.sockets_list)

            for notified_socket in read_sockets:

                # If the notified socket is a server socket,
                # then a new connection has been established
                if notified_socket == self.server_socket:
                    # Accept the new connection
                    client_socket, client_addr = self.server_socket.accept()

                    user = self._receive_message(client_socket)

                    # Client disconnected before entering a username
                    if user is False:
                        continue

                    if user['data'].decode(self.ENCODING) in self.clients.values():
                        message = 'User already exists'
                        self.send_error(client_socket, message)


                    # Add accepted socket to the sockets list
                    self.sockets_list.append(client_socket)

                    # Save the username and username header
                    self.clients[client_socket] = user

                    print('Accepted new connection from {}:{}, username: {}'
                          .format(*client_addr, user['data'].decode(self.ENCODING)))

                # Existing socket is sending a message
                else:

                    message = self._receive_message(notified_socket)

                    # Client disconnected
                    if message is False:
                        print("Closed connection from: {}"
                              .format(self.clients[notified_socket]['data'].decode(self.ENCODING)))

                        # Remove socket from socket list
                        self.sockets_list.remove(notified_socket)

                        # Remove user from client dictionary
                        del self.clients[notified_socket]

                        continue

                    # Get the user info
                    user = self.clients[notified_socket]

                    print(f"Received message from {user['data'].decode(self.ENCODING)}:"
                          + f"{message['data'].decode(self.ENCODING)}")

                    # Broadcast the message
                    self._broadcast(user, message, notified_socket)

            # Handle any socket exceptions from IO
            for notified_socket in exception_sockets:
                # Remove the faulty socket connection
                self.sockets_list.remove(notified_socket)

                # Remove the faulty client
                del self.clients[notified_socket]

    def stop(self):
        """Gracefully stop the chat service"""
        # Close all client sockets
        self._purge_connections()

        # Close the server socket
        self.server_socket.close()

