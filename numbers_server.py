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
                # if bytes_sent < len(welcome_msg.encode('utf-8')):
                #     handle_error(client_socket)
                #     connected_clients.remove(client_socket)
                #     sockets_data.pop(client_socket)
            else:
                if sockets_data[sock]["logged"] == 0:
                    # in the client make sure to send twice AFTER getting input for both user and pass
                    username = sock.recv(4096).decode('utf-8').split(":") # change later to recv all
                    password = sock.recv(4096).decode('utf-8').split(":")
                    if username[0] != "User" or password[0] != "Password":
                        handle_error(sock, connected_clients)

                    if check_credentials(username[1].strip(), password[1].strip(), user_dict): # successful login
                        success_msg = f"Hi {username[1].strip}, good to see you"
                        bytes_sent = sendall(sock, success_msg.encode('utf-8'))
                        sockets_data[sock]["logged"] = 1

                    else:
                        fail_msg = "Failed to login"
                        bytes_sent = sendall(sock, fail_msg.encode('utf-8'))
                else: # user is logged in and we can receive commands



def check_credentials(enteredUser, enteredPass, user_dict):
    if enteredUser not in list(user_dict.keys()):
        return False
    elif user_dict[enteredUser] == enteredPass:
        return True
    else:
        return False


def init_new_sock(sockets_data, sock):
    sockets_data[sock] = {}
    sockets_data[sock]["command"] = ""
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


def handle_error(sock, connected_clients):
    print("Error sending message!, closing client socket")
    connected_clients.remove(sock)
    sock.close()


def handle_login(socket, username, password, user_dict):
    flag = check_credentials(username, password, user_dict)

main()
