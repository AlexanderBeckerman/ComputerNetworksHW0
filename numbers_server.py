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

    user_dict = {}
    with open(user_file_path, 'r') as file:
        for line in file:
            # Split each line into username and password using tab as the delimiter
            username, password = line.strip().split('\t')

            # Add the username and password to the dictionary
            user_dict[username] = password

    print(user_dict)
