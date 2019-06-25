#!/usr/bin/env python3

# chat_server.py - service to be run on server host

import socket
import select

IP = '127.0.0.1'
PORT = 1234

ENCODING = 'utf-8'
HEADER_LENGTH = 10

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


server_socket.bind((IP, PORT))
server_socket.listen(10)

sockets_list = [server_socket]

# Stores socket as a key, user header and name as data
clients = {}

print(f'Listening for connections on {IP}:{PORT}...')


# Handles reception of messages
def receive_message(client_socket):

    try:
        # Receive the message header
        messaage_header = client_socket.recv(HEADER_LENGTH)

        # If no data was received then the client gracefully exited
        if not len(messaage_header):
            return False

        # Calculate the message length
        messaage_length = int(messaage_header.decode(ENCODING).strip())

        # Return a dictionary containing the message header and message data
        return {'header': messaage_header,
                'data': client_socket.recv(messaage_length)}

    except:
        # Client closed the connection in an unnatural manner
        return False


def broadcast(user, msg, conn):
    for client in clients:

        # Don't send to the src client
        if client != conn:

            # Send the user header and data
            # along with the message header and data
            client.send(user['header'] + user['data']
                        + message['header'] + message['data'])


while True:

    read_sockets, _, exception_sockets = select.select(sockets_list, [],
                                                       sockets_list)

    for notified_socket in read_sockets:

        # If the notified socket is a server socket,
        # then a new connection has been established
        if notified_socket == server_socket:
            # Accept the new connection
            client_socket, client_addr = server_socket.accept()

            user = receive_message(client_socket)

            # Client disconnected before entering a username
            if user is False:
                continue

            # Add accepted socket to the sockets list
            sockets_list.append(client_socket)

            # Save the username and username header
            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'
                  .format(*client_addr, user['data'].decode(ENCODING)))

        # Existing socket is sending a message
        else:

            message = receive_message(notified_socket)

            # Client disconnected
            if message is False:
                print("Closed connection from: {}"
                      .format(clients[notified_socket]['data'].decode(ENCODING)))

                # Remove socket from socket list
                sockets_list.remove(notified_socket)

                # Remove user from client dictionary
                del clients[notified_socket]

                continue

            # Get the user info
            user = clients[notified_socket]

            print(f"Received message from {user['data'].decode(ENCODING)}:"
                  + "{message['data'].decode(ENCODING)}")

            # Broadcast the message
            broadcast(user, message, notified_socket)

        # Handle any socket exceptions from IO
        for notified_socket in exception_sockets:

            # Remove the faulty socket connection
            sockets_list.remove(notified_socket)

            # Remove the faulty client
            del clients[notified_socket]
