from socket import *
import sys
import select


def main():
    args = sys.argv
    port = 1337
    sep = '\n'

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
    listeningSocket.listen()
    connected_clients = []
    awaiting_respone = []
    sockets_data = {}

    while True:
        readable, writable, e = select.select(connected_clients + [listeningSocket], awaiting_respone, [])

        for sock in readable:
            if sock == listeningSocket:
                client_socket, client_address = listeningSocket.accept()
                connected_clients.append(client_socket)
                init_new_sock(sockets_data, sock)
                welcome_msg = "Welcome! Please log in"
                bytes_sent = sendall(client_socket, welcome_msg.encode('utf-8'))
                if bytes_sent < len(welcome_msg.encode('utf-8')):
                    handle_error(client_socket)
                    connected_clients.remove(client_socket)
                    sockets_data.pop(client_socket)
            else:


def check_credentials(enteredUser, enteredPass, user_dict):
    if enteredUser not in list(user_dict.keys()):
        return False
    elif user_dict[enteredUser] == enteredPass:
        return True
    else:
        return False


def init_new_sock(sockets_data, sock):
    sockets_data[sock] = {}
    sockets_data[sock]["username"] = ""
    sockets_data[sock]["password"] = ""
    sockets_data[sock]["commend"] = ""
    sockets_data[sock]["logged"] = 0
    sockets_data[sock]["welcomed"] = 0


def sendall(sock, data):
    total = 0
    bytesleft = len(data)

    while total < len(data):
        bytesSent = sock.send(data[total:])
        if bytesSent == 0:
            break
        total += bytesSent
        bytesleft -= bytesleft

    return total


def recvall(sock):
    return


def handle_error(sock):
    print("Error sending message!, closing client socket")
    sock.close()


main()
