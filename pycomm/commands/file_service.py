import os
import select
import socket
import sys


class FileService:

    def __init__(self, host, port, path):
        self.HEADER_LENGTH = 10
        self.ENCODING = 'utf-8'

        self.host = host
        self.port = port

        self.ops = {}

        self.server_socket = None
        self.sockets_list = []

        self.storage_path = path

        # If the storage location does not exist then create it
        if not os.path.exists(self.storage_path):
            os.mkdir(self.storage_path)

    def _send_file(self, sock, size, file):
        """Used for sending files to a client"""
        print('Sending file to client...')

        # First create the file header
        file_header = f"{size:<{self.HEADER_LENGTH}}".encode(self.ENCODING)

        # Send the data
        sock.send(file_header + file)

    def _send_message(self, sock, message):
        """Used for sending general messages such as errors"""
        message = message.encode(self.ENCODING)
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode(self.ENCODING)

        # Send the message to the client socket
        sock.send(message_header + message)

    def _receive_message(self, client_socket):
        """Handles the reception of files"""
        try:
            # Retrieve the file header
            message_header = client_socket.recv(self.HEADER_LENGTH)

            # Client gracefully exited
            if not message_header:
                return None

            # Calculate the file length
            message_length = int(message_header.decode(self.ENCODING).strip())

            # Return a dict containing the file header and file data
            return {'header': message_header,
                    'data': client_socket.recv(message_length)}
        except:
            # Client closed the connection in an unnatural manner
            return None

    def start(self):
        """Enable the service"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.setblocking(False)
        self.server_socket.listen(5)

        self.sockets_list = [self.server_socket]

        print(f'Listening for connections on {self.host}:{self.port}...')

        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [],
                                                               self.sockets_list)

            for notified_socket in read_sockets:

                # If the notified socket is a server socket, then accept the connection
                if notified_socket == self.server_socket:
                    client_sock, client_addr = self.server_socket.accept()

                    # Client will first send the file operation
                    op_flag = self._receive_message(client_sock)

                    # If false - the client disconnected before sending the operation type
                    if op_flag is False:
                        continue

                    # Add the accepted socket to the sockets list
                    self.sockets_list.append(client_sock)

                    # Also add to the dictionary of operations to perform
                    self.ops[client_sock] = op_flag

                    print('\n\n[+]Accepted new connection from {}:{}'.format(*client_addr))
                    print("Operation: " + str(op_flag['data'].decode(self.ENCODING)))

                else:

                    # Receive the filename header and filename data
                    file = self._receive_message(notified_socket)

                    if file:
                        print("File name: " + str(file['data'].decode(self.ENCODING)))

                    # Client disconnected
                    if not file:
                        print('[-]Closed connection from {}:{}'.format(*client_addr))

                        # Remove from socket list
                        self.sockets_list.remove(notified_socket)

                        # Also remove from operations dictionary
                        del self.ops[notified_socket]

                        continue

                    # Store the title name of the file
                    file = file['data'].decode(self.ENCODING)

                    # Get the operation to perform
                    current_operation = self.ops[notified_socket]
                    current_operation = current_operation['data'].decode(self.ENCODING)

                    # Client is requesting a file
                    if current_operation == 'receive':

                        file_path = os.path.join(self.storage_path, file)

                        # If the file does not exist inform the client and continue listening
                        if not os.path.isfile(os.path.join(file_path)):
                            message = 'File Not Found'
                            self._send_message(notified_socket, message)
                            # print("Thread started")
                            continue

                        else:
                            # The file exists so send a status report to the client
                            message = 'File Exists'
                            self._send_message(notified_socket, message)

                        # Read the file before sending to the client
                        with open(file, 'rb') as f_obj:
                            file_size = os.path.getsize(file_path)
                            data = f_obj.read(file_size)

                        self._send_file(notified_socket, file_size, data)

