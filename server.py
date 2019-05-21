#! venv/bin/python3
#
# Server protocol and socket handling. Allows for multiple clients
# with unique games to all play at once using selectors module and creating
# a new ServerGame instance. 
#
#

import socket
from game import ServerGame
import selectors
import sys

sel = selectors.DefaultSelector()
active_games = {}

host = ''
# get the port number from command line if supplied
if len(sys.argv) > 1:
    port = int(sys.argv[1])
    if port <= 1024 or port > 65535:
        print("Port Number outside of useable range", flush=True)
        raise ValueError
else:
    port = 23456

EOM = b'\x0A'


def accept_wrapper(key, mask):
    sock = key.fileobj
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr, flush=True)
    conn.setblocking(False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, service_connection)
    active_games[conn] = ServerGame()   #create a unique game per connection

def service_connection(key, mask):
    sock = key.fileobj
    out_msg = None
    if active_games[sock].hit_count==14:
        if mask & selectors.EVENT_WRITE:
            sock.sendall(str(active_games[sock].turns_taken).encode('ascii')+EOM)
            print(
                "Game with ",
                sock.getpeername(),
                " finished in ",
                active_games[sock].turns_taken,
                " moves",
                flush=True
            )
            del active_games[sock]
            sel.unregister(sock)
            sock.close()

    elif active_games[sock].running:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                messages = recv_data.split(EOM)
                if messages[-1]==b'' and len(messages)>1:
                    messages = messages[:-1]
                for message in messages:
                    turn_taken = active_games[sock].shot_fired(message.decode('ascii'))
                    if turn_taken:
                        sock.sendall(turn_taken.encode('ascii') + EOM)
                        print(
                            'Turn ',
                            message.decode('ascii'),
                            ' taken by ',
                            sock.getpeername(),
                            ' was a ',
                            turn_taken,
                            flush=True
                        )
                    else:
                        print('Invalid command received. Closing connection: ', sock, flush=True)
                        sel.unregister(sock)
                        sock.close()

            else:
                print('closing connection to', sock.getpeername(), flush=True)
                sel.unregister(sock)
                sock.close()
    else:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)
            messages = recv_data.split(EOM)
            if messages[0]==b'START GAME':
                sock.sendall('POSITIONING SHIPS'.encode('ascii')+EOM)
                active_games[sock].setup_ship_placement()
                sock.sendall('SHIPS IN POSITION'.encode('ascii')+EOM)
                active_games[sock].print_board()
            elif recv_data:
                print('Invalid command received. Closing connection: ', sock, flush=True)
                sel.unregister(sock)
                sock.close()
            else:
                print('Connection closed by client: ', sock.getpeername(), flush=True)
                sel.unregister(sock)
                sock.close()


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
