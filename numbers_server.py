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

