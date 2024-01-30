#!/usr/bin/python3

import struct
from socket import *
import sys
import errno

MSG_LEN_HEADER = 2
ERR_MSG = "ERROR IN HANDLING CLIENT, CLOSING CONNECTION..."


def main():
    args = sys.argv
    hostname = ''
    port = ''

    if len(args) == 1:
        hostname = 'localhost'
        port = 1337
    elif len(args) == 3:
        hostname = args[1]
        port = int(args[2])
    else:
        print("ERROR IN ARGS COUNT!, EXITING")
        exit(1)

    client_socket = socket(AF_INET, SOCK_STREAM)

    try:
        client_socket.connect((hostname, port))
        print("connected to server")
        print(receive_message(client_socket))

    except OSError as e:
        if e.errno == errno.ECONNREFUSED:
            print("Server refused connection")
            exit(1)
        else:
            print(error.strerror)
            exit(1)

    while True:  # authentication loop
        username = input()
        password = input()
        user_pass = username + ":" + password  # we turn it into this format so we can handle it in the server
        send_message(user_pass, client_socket)
        login_msg = receive_message(client_socket)
        success = "Hi " + str(username.strip().split(":")[1]) + ", good to see you."
        if login_msg == "OK":
            print(success)
            break
        else:
            print("Failed to login.")

    while True:  # sending commands loop
        command = input()
        send_message(command, client_socket)
        if command == 'quit':
            client_socket.close()
            exit(0)
        print(receive_message(client_socket))


def recvall(client_socket, data_len):
    total = 0
    bytes_left = data_len
    bytes_read = b''
    while total < data_len:
        try:
            bytes_read += client_socket.recv(bytes_left)
        except OSError:
            return 0
        total += len(bytes_read)
        bytes_left -= len(bytes_read)
    return bytes_read


def sendall(sock, data):
    total = 0
    bytesleft = len(data)

    while total < len(data):
        try:
            bytesSent = sock.send(data[total:])
        except OSError:
            return 0
        total += bytesSent
        bytesleft -= bytesSent

    return total


def receive_message(client_socket):
    bytes_received = recvall(client_socket, MSG_LEN_HEADER)  # get the welcome message length
    msg_len = struct.unpack(">h", bytes_received[:2])[0]
    msg = recvall(client_socket, msg_len).decode()
    if len(msg) == 0 or msg == ERR_MSG:
        print("ERROR READING MESSAGE, CLOSING CONNECTION")
        client_socket.close()
        exit(1)
    return msg


def send_message(message, client_socket):
    message = message.encode()
    data_to_send = struct.pack(">h", len(message)) + message
    bytes_sent = sendall(client_socket, data_to_send)
    if bytes_sent == 0:
        print("ERROR SENDING MESSAGE, CLOSING CONNECTION")
        client_socket.close()
        exit(1)


main()