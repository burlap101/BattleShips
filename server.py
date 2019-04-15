#! venv/bin/python3

import socket
from game import ServerGame
import secrets
import selectors

sel = selectors.DefaultSelector()
active_games = {}

host = ''
port = 23456

def accept_wrapper(key, mask):
    sock = key.fileobj
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, service_connection)
    active_games[conn] = ServerGame()   #create a unique game per connection

def service_connection(key, mask):
    sock = key.fileobj
    out_msg = None
    if active_games[sock].hit_count==14:
        if mask & selectors.EVENT_WRITE:
            sock.sendall(str(active_games[sock].turns_taken).encode('ascii'))
            print(
                "Game with ",
                sock.getpeername(),
                " finished in ",
                active_games[sock].turns_taken,
                " moves"
            )
            del active_games[sock]
            sel.unregister(sock)
            sock.close()

    elif active_games[sock].running:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                turn_taken = active_games[sock].shot_fired(recv_data.decode('ascii'))
                if turn_taken:
                    out_msg = turn_taken.encode('ascii')
            else:
                print('closing connection to', sock.getpeername())
                sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if out_msg:
                sent = sock.send(out_msg)  # Should be ready to write
                out_msg = out_msg[sent:]
    elif active_games[sock].initialised==False:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(len("START GAME"))
            if recv_data.decode('ascii')=="START GAME":
                sock.sendall('POSITIONING SHIPS'.encode('ascii'))
                active_games[sock].setup_ship_placement()
                sock.sendall('SHIPS IN POSITION'.encode('ascii'))
                active_games[sock].print_board()
            elif recv_data:
                print('Invalid command received. Closing connection: ', sock)
                sel.unregister(sock)
                sock.close()
            else:
                print('Connection closed by client: ', sock.getpeername())
                sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if out_msg:
                sent = sock.send(out_msg)    # Keep track of sent data bytes
                out_msg = out_msg[sent:]
    else:
        out_msg = str(active_games[sock].turns_taken).encode('ascii')
        if mask & selectors.EVENT_WRITE:
            sent = sock.send(out_msg)    # Keep track of sent data bytes
            out_msg = out_msg[sent:]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((host, port))
    server_socket.setblocking(False)
    server_socket.listen()
    events = selectors.EVENT_READ
    sel.register(server_socket, events, accept_wrapper)
    while True:
        for key, mask in sel.select(timeout=None):
            callback = key.data
            callback(key, mask)
