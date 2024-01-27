#!/usr/bin/python3

import errno
import struct
from socket import *
import sys
import select

MSG_LEN_HEADER = 2
ERROR_MSG = "ERROR IN HANDLING CLIENT, CLOSING CONNECTION..."


def main():
    args = sys.argv
    port = 1337

    if len(args) != 2 and len(args) != 3:
        print("error in args count")
        exit(1)

    if len(args) == 3:
        port = args[2]
    user_file_path = args[1]

    user_dict = {}
    try:
        with open(user_file_path, 'r') as file:
            for line in file:
                # Split each line into username and password using tab as the delimiter
                username, password = line.strip().split()
                # Add the username and password to the dictionary
                user_dict[username] = password
    except:
        print("error reading file!")
        exit(1)
    try:
        listeningSocket = socket(AF_INET, SOCK_STREAM)
        listeningSocket.bind(('', port))
        listeningSocket.listen(5)
    except:
        print("Error creating socket")
        listeningSocket.close()
        exit(1)

    connected_clients = []
    sockets_data = {}

    while True:
        readable, w, e = select.select(connected_clients + [listeningSocket], [], [])
        print(connected_clients)
        for sock in readable:
            if sock == listeningSocket:
                client_socket, client_address = listeningSocket.accept()
                connected_clients.append(client_socket)
                init_new_sock(sockets_data, client_socket.fileno())
                msg = "Welcome! Please log in"
                welcome_msg = struct.pack('>h', len(msg)) + msg.encode()
                bytes_sent = sendall(client_socket, welcome_msg)
                if bytes_sent < len(welcome_msg):
                    handle_error(client_socket, connected_clients, sockets_data)
                    sockets_data.pop(client_socket.fileno())
            else:
                try:
                    if sockets_data[sock.fileno()]['data_length'] == 0:  # if we have yet to get the incoming data size
                        print("received new data from client!")
                        try:
                            data = sock.recv(MSG_LEN_HEADER)  # get the bytes that contain the message length
                        except:
                            handle_error(sock, connected_clients, sockets_data)  # if the client closed the connection
                            continue
                        data_len = struct.unpack(">h", data[:MSG_LEN_HEADER])[0]  # get the message length
                        sockets_data[sock.fileno()]['data_length'] = data_len

                    bytes_to_read = sockets_data[sock.fileno()]['data_length'] - len(
                        sockets_data[sock.fileno()]['data_read'])
                    if bytes_to_read > 0:  # check if we need to recv from the socket
                        try:
                            data_received = sock.recv(
                                bytes_to_read)  # receive each time the amount of data we have left to read
                        except:
                            handle_error(sock, connected_clients, sockets_data)
                            continue

                        sockets_data[sock.fileno()]['data_read'] += data_received
                        bytes_to_read -= len(data_received)

                    if bytes_to_read == 0:  # if we got the entire message, handle it
                        data = sockets_data[sock.fileno()]['data_read'].decode()
                        print(data)
                        if data == "quit":
                            handle_error(sock, connected_clients, sockets_data)
                            continue
                        response = handle_response(data, user_dict, sockets_data, sock)
                        if response == ERROR_MSG:
                            handle_error(sock, connected_clients, sockets_data)
                            continue
                        response = response.encode()
                        data_to_send = struct.pack(">h",
                                                   len(response)) + response  # concatenate our response size with the response
                        bytes_sent = sendall(sock,
                                             data_to_send)  # Yonatan said we can assume this doesn't block so we send here
                        if bytes_sent < len(data_to_send):
                            handle_error(sock, connected_clients, sockets_data)
                            sockets_data.pop(sock.fileno())
                            continue
                        sockets_data[sock.fileno()][
                            'data_read'] = b''  # reset the entry when we are done handling the response
                        sockets_data[sock.fileno()]['data_length'] = 0
                except:
                    handle_error(sock, connected_clients, sockets_data)


def check_credentials(enteredUser, enteredPass, user_dict):
    if enteredUser not in list(user_dict.keys()):
        return False
    if user_dict[enteredUser] == enteredPass:
        return True
    return False


def init_new_sock(sockets_data, sock):
    sockets_data[sock] = {}
    sockets_data[sock]["data_read"] = b''
    sockets_data[sock]["data_length"] = 0
    sockets_data[sock]["logged"] = 0


def sendall(sock, data):
    total = 0
    bytesleft = len(data)

    while total < len(data):
        try:
            bytesSent = sock.send(data[total:])
        except:
            return 0
        total += bytesSent
        bytesleft -= bytesSent

    return total


def handle_error(sock, connected_clients, sockets_data):
    print(ERROR_MSG)
    data_to_send = struct.pack(">h", len(ERROR_MSG.encode())) + ERROR_MSG.encode()
    sendall(sock, data_to_send)
    connected_clients.remove(sock)
    sockets_data.pop(sock.fileno())
    sock.close()


def handle_response(user_input, user_dict, sockets_data, sock):
    if ":" not in user_input:
        return ERROR_MSG
    new_input = user_input.strip().split(":")
    if len(new_input) == 4 and new_input[0] == "User" and new_input[2] == "Password":  # auth attempt by client
        username = new_input[1]
        password = new_input[3]
        if check_credentials(username, password, user_dict):
            sockets_data[sock.fileno()]['logged'] = 1
            return "OK"
        else:
            return "Failed to login."
    elif len(new_input) == 2 and sockets_data[sock.fileno()]['logged'] == 1:  # else if it's a command to the server
        command = new_input[0]
        command_input = new_input[1].strip()
        return handle_command(command, command_input)

    else:
        return ERROR_MSG


def handle_command(command, command_input):
    if command == "calculate":
        if parse_calculate(command_input) == ERROR_MSG:
            return ERROR_MSG
        else:
            x, y, z = parse_calculate(command_input.replace(" ", ""))
            if y == '/' and z == '0': # check for division by zero
                return ERROR_MSG
            return calculate(int(x), y, int(z))

    elif command == "is_palindrome":
        if parse_is_palindrome_or_primary(command_input) == ERROR_MSG:
            return ERROR_MSG
        else:
            x = parse_is_palindrome_or_primary(command_input)
            return is_palindrome(x)

    elif command == "is_primary":
        if parse_is_palindrome_or_primary(command_input) == ERROR_MSG:
            return ERROR_MSG
        else:
            x = parse_is_palindrome_or_primary(command_input)
            return is_primary(int(x))

    else:
        return ERROR_MSG


# ---- COMMAND HANDLING FUNCTIONS ----
def calculate(x, y, z):
    if y == '+':
        st_answer = "Response: " + str(x + z) + "."
        return st_answer
    if y == '-':
        st_answer = "Response: " + str(x - z) + "."
        return st_answer
    if y == '*':
        st_answer = "Response: " + str(x * z) + "."
        return st_answer
    if y == '/':
        st_answer = "Response: " + str(x / z) + "."
        return st_answer


def is_palindrome(x):
    if (str(x) == str(x)[::-1]):
        return "Response: Yes."
    else:
        return "Response: No."


def is_primary(x):
    if x <= 1:
        return "Response: No."

    for i in range(2, int(x ** 0.5) + 1):
        if x % i == 0:
            return "Response: No."

    return "Response: Yes."


def parse_calculate(input):
    print("inside parse calc")
    x = ""
    y = ""
    z = ""
    s = 0
    for i in range(len(input)):
        if i == 0 and input[0] == '-':
            x += input[0]
            continue
        if input[i].isdigit():
            x = x + input[i]
        elif input[i] == '+' or input[i] == '-' or input[i] == '/' or input[i] == '*':
            y = input[i]
            s = i
            break
        else:
            return ERROR_MSG
    s += 1
    for i in range(s, len(input)):
        if i == s and input[s] == '-':
            z += input[s]
            continue
        if input[i].isdigit():
            z = z + input[i]
        else:
            return ERROR_MSG

    if y == "" or z == "":
        return ERROR_MSG

    return x, y, z


def parse_is_palindrome_or_primary(input):
    for char in input:
        if char.isdigit() == False:
            return ERROR_MSG

    return input


main()
