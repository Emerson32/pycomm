import click
import errno
import socket
import sys


class FileClient:
    
    def __init__(self, host, port, file, path, file_op):
        self.host = host
        self.port = port
        self.file_name = file
        self.storage_path = path
        self.file_op = file_op
        
        self.HEADER_LENGTH = 10
        self.ENCODING = 'utf-8'
        
        self.client_socket = None

    def _receive_file(self):
        """Used for receiving files from a service"""
        print("Receiving file...")

        try:
            # Retrieve the file size
            file_header = self.client_socket.recv(self.HEADER_LENGTH)

            # Header not received
            if not file_header:
                print("Could not retrieve header")
                sys.exit()

            # Receive the file data
            file_size = int(file_header.decode(self.ENCODING).strip())
            data = self.client_socket.recv(file_size)

            # Begin writing
            with open(self.file_name, 'wb') as f_obj:
                f_obj.write(data)

        except Exception as e:
            print(e)
            sys.exit()



    def send_file_info(self):
        # First send the op flag so that the server will know what to do
        op_flag = self.file_op.encode(self.ENCODING)
        op_header = f"{len(op_flag): <{self.HEADER_LENGTH}}".encode(self.ENCODING)

        self.client_socket.send(op_header + op_flag)

        # Encode the title
        title = self.file_name.encode(self.ENCODING)

        # Form the title header and send the data
        title_header = f"{len(title): <{self.HEADER_LENGTH}}".encode(self.ENCODING)

        self.client_socket.send(title_header + title)

    def retrieve_status(self):
        try:
            status_header = self.client_socket.recv(self.HEADER_LENGTH)

            if not status_header:
                return None

            status_length = int(status_header.decode(self.ENCODING).strip())

            status = self.client_socket.recv(status_length)
            status = status.decode(self.ENCODING)

            if status == 'File Exists':
                print("File Found\n")
                return True

            else:
                print("File Not Found!")
                return False
        except:
            return None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.client_socket.setblocking(True)

        try:
            if self.file_op == 'receive':
                self.send_file_info()
                if self.retrieve_status():
                    # Receive the file and write it
                    self._receive_file()
                    print("Done")

                else:
                    sys.exit()

            elif self.file_op == 'send':
                # File existence already checked in this case
                pass

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                sys.exit()

        except Exception as e:
            # Any other exception - something happened, exit
            print('Reading error: '.format(str(e)))
            sys.exit()

