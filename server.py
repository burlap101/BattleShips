#! /usr/bin/python3

import socket
from game import BattleShips
import secrets

host = ''
print(host)
port = 23456
waiting_code = secrets.token_bytes(8)  # Randomly generated sequence of bytes to set msg buffer to indicate waiting

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((host, port))
    server_socket.listen()
    print('Awaiting connections')
    conn, addr = server_socket.accept()
    with conn:
        game = BattleShips()
        print('Connected to client at address ', addr)

        while True:
            in_msg = conn.recv(1024)

            if in_msg.decode('ascii')=="START GAME":
                out_msg = 'POSITIONING SHIPS\n'
                #conn.sendall(out_msg.encode('ascii'))
                game.setup_ship_placement()
                game.print_board()
                out_msg += 'SHIPS IN POSITION'
                conn.sendall(out_msg.encode('ascii'))
                in_msg = waiting_code
            elif not in_msg:
                print('Connection at address ', addr,' closed by client')
                break
            elif game.running():
                turn_taken = game.shot_fired(in_msg.decode('ascii').upper())
                if turn_taken:
                    conn.sendall(turn_taken.encode('ascii'))
                    print('\nTurn Taken: ',in_msg.decode('ascii').upper(),' it was a ',turn_taken,'\n')
                    game.print_board()
                    if not game.running():
                        out_msg = 'You have sunk all the battleships. Thanks.'
                        conn.sendall(out_msg.encode('ascii'))
                        conn.close()
                        break
                else:
                    out_msg = 'Invalid Coordinates'
                    conn.sendall(out_msg.encode('ascii'))
                in_msg = waiting_code
            elif in_msg==waiting_code:
                pass
            else:
                out_msg = 'Unrecognised command'
                conn.sendall(out_msg.encode('ascii'))
                in_msg = waiting_code




