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

    def _enumerate_list(self):
        """Creates a list of all the storage files on the server"""
        file_list = []

        for _, _, filenames in os.walk(self.storage_path, topdown=True):
            for name in filenames:
                file_list.append(name)

        return file_list

    def _send_file(self, sock, file):
        """Used for sending files to a client"""

        file_path = os.path.join(self.storage_path, file)

        # If the file does not exist inform the client and continue listening
        if not os.path.isfile(os.path.join(file_path)):
            message = 'File Not Found'
            self._send_message(sock, message)
            return

        else:
            # The file exists so send a status report to the client
            message = 'File Exists'
            self._send_message(sock, message)

        # Read the file before sending to the client
        with open(file, 'rb') as f_obj:
            file_size = os.path.getsize(file_path)
            file_data = f_obj.read(file_size)
        print('Sending file to client...')

        # First create the file header
        file_header = f"{file_size:<{self.HEADER_LENGTH}}".encode(self.ENCODING)

        # Send the data
        sock.send(file_header + file_data)
        print("File Sent")

    def _receive_file(self, sock, filename):
        """Used for receiving a file from a client"""
        print("[+] Receiving file...")
        status = ''

        try:
            # Retrieve the file size
            file_header = sock.recv(self.HEADER_LENGTH)

            # Header not received
            if not file_header:
                print("[!] Could not retrieve header")
                sys.exit()

            # Receive the file data
            file_size = int(file_header.decode(self.ENCODING).strip())
            data = sock.recv(file_size)

            # Begin writing file to local storage
            with open(filename, 'wb') as f_obj:
                f_obj.write(data)

            print("[+] Done")

        except Exception:
            print("[-] Could not receive file!")
            sys.exit()

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

    def _remove_connection(self, addr, sock):
        print('[-]Closed connection from {}:{}'.format(*addr))

        # Remove from socket list
        self.sockets_list.remove(sock)

        # Also remove from operations dictionary
        del self.ops[sock]

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
                    # Get the operation to perform
                    current_operation = self.ops[notified_socket]
                    current_operation = current_operation['data'].decode(self.ENCODING)

                    # Client is requesting a list of files stored on the server
                    if current_operation == 'list':
                        files = self._enumerate_list()

                        # Form the message to be sent to the client
                        files_message = 'Files Stored:\n-------------\n'
                        for file in files:
                            files_message += file + '\n'

                        self._send_message(notified_socket, files_message)
                        self._remove_connection(client_addr, notified_socket)

                        continue

                    else:

                        # Receive the filename header and filename data
                        file = self._receive_message(notified_socket)

                        if file:
                            print("File name: " + str(file['data'].decode(self.ENCODING)))

                        # Client disconnected
                        if not file:
                            self._remove_connection(client_addr, notified_socket)

                            continue

                        # Store the title name of the file
                        file_name = file['data'].decode(self.ENCODING)

                    # Client is requesting a file
                    if current_operation == 'receive':

                        # Includes necessary file checks
                        self._send_file(notified_socket, file_name)

                    # Client is sending a file
                    else:
                        self._receive_file(notified_socket, file_name)

    def stop(self):
        # Close all client sockets
        self._purge_connections()

        # Close the server socket
        self.server_socket.close()







