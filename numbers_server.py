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
    with open(user_file_path, 'r') as file:
        for line in file:
            # Split each line into username and password using tab as the delimiter
            username, password = line.strip().split()
            # Add the username and password to the dictionary
            user_dict[username] = password

    listeningSocket = socket(AF_INET, SOCK_STREAM)
    listeningSocket.bind(('', port))
    listeningSocket.listen(5)
    connected_clients = []
    sockets_data = {}

    while True:
        readable, w, e = select.select(connected_clients + [listeningSocket], [], [])

        for sock in readable:
            if sock == listeningSocket:
                client_socket, client_address = listeningSocket.accept()
                connected_clients.append(client_socket)
                init_new_sock(sockets_data, sock)
                welcome_msg = "Welcome! Please log in"
                bytes_sent = sendall(client_socket, welcome_msg.encode())
                if bytes_sent < len(welcome_msg.encode()):
                    handle_error(client_socket, connected_clients)
                    sockets_data.pop(client_socket)
            else:
                if sockets_data[sock]['data_length'] == -1:  # if we have yet to get the incoming data size
                    data = sock.recv(MSG_LEN_HEADER)  # get the bytes that contain the message length
                    if len(data) == 0:
                        handle_error(sock, connected_clients)  # if the client closed the connection
                        continue
                    data_len = struct.unpack(">H", data[:MSG_LEN_HEADER])  # get the message length
                    sockets_data[sock]['data_length'] = data_len

                bytes_to_read = sockets_data[sock]['data_length'] - len(sockets_data[sock]['data_read'])
                if bytes_to_read > 0:
                    data_received = sock.recv(
                        bytes_to_read)  # receive each time the amount of data we have left to read
                    if data_received == 0:
                        handle_error(sock, connected_clients)
                        sockets_data.pop(sock)
                        continue

                    sockets_data[sock]['data_read'] += data_received
                    bytes_to_read -= len(data_received)

                if bytes_to_read == 0:  # if we got the entire message, handle it
                    data = sockets_data[sock]['data_read'].decode()
                    if data == "quit":
                        connected_clients.remove(sock)
                        sockets_data.pop(sock)
                        sock.close()
                        continue
                    response = handle_response(data, user_dict)
                    if response == ERROR_MSG:
                        handle_error(sock, connected_clients)
                        sockets_data.pop(sock)
                        continue
                    response = response.encode()
                    data_to_send = struct.pack(">H", len(response)) + response # concatenate our response size with the response
                    bytes_sent = sendall(sock, data_to_send) # Yonatan said we can assume this doesn't block so we send here
                    if bytes_sent < len(data_to_send):
                        handle_error(sock, connected_clients)
                        sockets_data.pop(sock)
                        continue
                    sockets_data[sock]['data_read'] = b''  # reset the entry when we are done handling the response
                    sockets_data[sock]['data_length'] = -1


def check_credentials(enteredUser, enteredPass, user_dict):
    if enteredUser not in list(user_dict.keys()):
        return False
    elif user_dict[enteredUser] == enteredPass:
        return True
    else:
        return False


def init_new_sock(sockets_data, sock):
    sockets_data[sock] = {}
    sockets_data[sock]["data_read"] = b''
    sockets_data[sock]["data_length"] = -1  # default value


def sendall(sock, data):
    total = 0
    bytesleft = len(data)

    while total < len(data):
        bytesSent = sock.send(data[total:])
        if bytesSent == 0:
            return 0  # if 0 bytes were sent it means the connection was closed
        total += bytesSent
        bytesleft -= bytesSent

    return total


def handle_error(sock, connected_clients):
    print(ERROR_MSG)
    connected_clients.remove(sock)
    sock.close()


def handle_response(user_input, user_dict):
    if ":" not in user_input:
        return ERROR_MSG
    new_input = user_input.strip().split(":")
    if len(new_input) == 4:  # authentication attempt from client
        username = new_input[1]
        password = new_input[3]
        if check_credentials(username, password, user_dict):
            return f"Hi {username}, good to see you."
        else:
            return "Failed to login."
    elif len(new_input) == 2:  # else if it's a command to the server
        command = new_input[0]
        command_input = new_input[1]
        return handle_command(command, command_input)

    else:
        return ERROR_MSG


def handle_command(command, command_input):
    if command == "calculate":
        if parse_calculate(command_input) == ERROR_MSG:
            return ERROR_MSG
        else:
            x, y, z = parse_calculate(command_input)
            return calculate(int(x), y, int(z))

    elif command == "is_palindrome":
        if parse_is_palindrome_or_primary(command_input) == ERROR_MSG:
            return ERROR_MSG
        else:
            x = parse_is_palindrome_or_primary(command_input)
            return is_palindrome(int(x))

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
    if z == '+':
        st_answer = "Response: " + str(x + y) + "."
        return st_answer
    if z == '-':
        st_answer = "Response: " + str(x - y) + "."
        return st_answer
    if z == '*':
        st_answer = "Response: " + str(x * y) + "."
        return st_answer
    if z == '/':
        st_answer = "Response: " + str(x / y) + "."
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
    x = ""
    y = ""
    z = ""
    s = 0
    for i in range(len(input)):
        if input[i].isdigit():
            x = x + input[i]
            s += 1
        elif input[i] == '+' or input[i] == '-' or input[i] == '/' or input[i] == '*':
            y = input[i]
            s += 1
            break
        else:
            return ERROR_MSG

    for i in range(s, len(input)):
        if input[i].isdigit():
            z = z + input[i]
        else:
            return ERROR_MSG

    if y == "" or z == "":
        return ERROR_MSG

    return x, y, z


def parse_is_palindrome_or_primary(input):
    x = ""
    for char in input:
        if char.isdigit() == False:
            return ERROR_MSG

    return input


main()
