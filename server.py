#! venv/bin/python3

import socket
from game import ServerGame
import secrets
import selectors

sel = selectors.DefaultSelector()
active_games = {}

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
    data = key.data
    if active_games[sock].running:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                print('closing connection to', data.addr)
                sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print('echoing', repr(data.outb), 'to', data.addr)
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]
    elif active_games[sock].initialised==False:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(len("START GAME"))
            if recv_data.decode('ascii')=="START GAME":
                sock.sendall('POSITIONING SHIPS'.encode('ascii'))
                active_games[sock].setup_ship_placement()
                sock.sendall('SHIPS IN POSITION'.encode('ascii'))
            elif recv_data:
                print('Invalid command received. Closing connection: ', sock)
                sock.close()
            else:
                print('Connection closed by client: ', sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                sent = sock.send(data.outb)    # Keep track of sent data bytes
                data.outb = data.outb[sent:]
    else:
        data.outb = str(active_games[sock].turns_taken).encode('ascii')
        if mask & selectors.EVENT_WRITE:
            sent = sock.send(data.outb)    # Keep track of sent data bytes
            data.outb = data.outb[sent:]


host = ''
port = 23456

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
