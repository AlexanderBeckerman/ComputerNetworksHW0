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
                bytes_sent = sendall(client_socket, welcome_msg.encode('utf-8'))
                if bytes_sent < len(welcome_msg.encode('utf-8')):
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
                    data_recieved = sock.recv(bytes_to_read)  # receive each time the amount of data we have left to read
                    if data_recieved == 0:
                        handle_error(sock, connected_clients)
                        sockets_data.pop()
                        continue

                    sockets_data[sock]['data_read'] += data_recieved
                    bytes_to_read -= len(data_recieved)

                if bytes_to_read == 0:  # if we got the entire message, handle it
                    data = sockets_data[sock]['data_read'].decode()
                    response = handle_response(data, user_dict)
                    if response == ERROR_MSG:
                        handle_error(sock, connected_clients)
                        sockets_data.pop(sock)
                        continue
                    response = response.encode()
                    data_to_send = struct.pack(">H", len(response)) + response
                    bytes_sent = sendall(sock, data_to_send)
                    if bytes_sent < len(data_to_send):
                        handle_error(sock, connected_clients)
                        sockets_data.pop(sock)
                        continue
                    sockets_data[sock]['data_read'] = b'' # reset the entry when we are done handling the response
                    sockets_data[sock]['data_length'] = -1

                data = recvall(sock, sockets_data[sock]['data_length'])
                data = data.decode()


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
        bytesleft -= bytesleft

    return total


def recvall(sock, data_length):
    return


def handle_error(sock, connected_clients):
    print(ERROR_MSG)
    connected_clients.remove(sock)
    sock.close()


def handle_login(socket, username, password, user_dict):
    flag = check_credentials(username, password, user_dict)


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
        x, y, z = parse_calcualte(command_input)
        return calculate(x, y, z)
    elif command == 'is_palindrome':
        return is_palindrome(command_input)
    elif command == "is_primary":
        return is_primary(command_input)


def calculate(x, y, z):
    ## do we need to check if the input is correct?
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
    ## do we need to check if the input is correct?
    if (str(x) == str(x)[::-1]):
        return "Response: Yes."
    else:
        return "Response: No."


def is_primary(x):
    ## do we need to check if the input is correct?
    if x <= 1:
        return "Response: No."

    for i in range(2, int(x ** 0.5) + 1):
        if x % i == 0:
            return "Response: No."

    return "Response: Yes."


main()
