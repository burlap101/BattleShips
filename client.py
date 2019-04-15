#! venv/bin/python3

import socket
from game import ClientGame
import secrets

host = '127.0.0.1'
port = 23456
waiting_code = secrets.token_bytes(8)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # TCP socket setup
    print('attempting to connect')
    s.connect((host,port))
    print('connected to {}:{}'.format(host,port))
    s.sendall('START GAME'.encode('ascii'))

    response = s.recv(len('POSITIONING SHIPS'))  # retrieve characters from buffer same length as expected message
    print(response.decode('ascii'))
    response = s.recv(len('SHIPS IN POSITION'))
    print(response.decode('ascii'))
    game = ClientGame()
    remaining = ''
    while True:
        game.print_board()
        if remaining and game.hit_count==14:
            print(remaining)
            break
        elif game.hit_count==14:
            response = s.recv(4)
            print(response.decode('ascii'))
            break
        command = input('Enter coord: ')
        if command and game._validate_coords(command.upper()):
            bytes_sent = s.send(command.upper().encode('ascii'))
            if bytes_sent==len(command):
                response = s.recv(1024)
                if not response:
                    print('connection closed by server')
                    break
                response = response.decode('ascii')
                remaining = game.shot_fired(command.upper(), response)

                if remaining:
                    turns_returned = int(remaining)
                    print(response[:-len(remaining)])
                else:
                    print(response)
        else:
            print('Invalid coordinates')
