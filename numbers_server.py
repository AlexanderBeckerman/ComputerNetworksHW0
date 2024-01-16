from socket import *
import sys

def main():

    args = sys.argv
    port = 1337

    if len(args) != 2 or len(args) != 3:
        print("error in args count")
        exit(1)

    if len(args) == 3:
        port = args[2]
    user_file_path = args[1]

def check_credentials(path, enteredUser, enteredPass):
    user_dict = {}
    with open(path, 'r') as file:
        for line in file:
            # Split each line into username and password using tab as the delimiter
            username, password = line.strip().split()

            # Add the username and password to the dictionary
            user_dict[username] = password

    if enteredUser not in list(user_dict.keys()):
        print("wrong user name")
    elif user_dict[enteredUser] == enteredPass:
        print ("log in - successfull")
    else:
        print("wrong password")


check_credentials("users_file.txt", "Daniel", "BetT3RpAas")