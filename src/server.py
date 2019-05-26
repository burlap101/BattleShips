#! venv/bin/python3
#
# Server protocol and socket handling. Allows for multiple clients
# with unique games to all play at once using selectors module and creating
# a new ServerGame instance.
# Achieved using selectors and non-blocking sockets (server doesn't 'hang' to wait for a response
# from the client instead polls all open sockets).

import selectors
import socket
import sys

from server_crypto import ServerCrypto
from server_game import ServerGame

sel = selectors.DefaultSelector()
# an empty dictionary to hold all game instances
active_games = {}

# an empty dictionary to manage all per connection specific encryption
crypto = {}

# an empty dictionary to hold the key and iv for decryption of the board by the client after completion
board_key_iv = {}
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
    # function for accepting all connections from hte clients
    sock = key.fileobj
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr, flush=True)
    conn.setblocking(False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, service_connection)
    active_games[conn] = ServerGame()  # create a unique game per connection
    crypto[conn] = ServerCrypto()


def service_connection(key, mask):
    # function services the connections using a series of conditional statements
    # and monitoring expected communications from the clients
    sock = key.fileobj
    out_msg = None
    if active_games[sock].hit_count == 14 and active_games[sock].game_completed == False:
        if mask & selectors.EVENT_WRITE:
            # Encrypt using fernet prior to sending
            token = crypto[sock].encrypt_msg_fernet(str(active_games[sock].turns_taken).encode('ascii') + EOM)
            sock.sendall(token)
            print(
                "Game with ",
                sock.getpeername(),
                " finished in ",
                active_games[sock].turns_taken,
                " moves",
                flush=True
            )
            active_games[sock].running = False
            active_games[sock].game_completed = True

    elif active_games[sock].running:
        if mask & selectors.EVENT_READ:
            # Encrypted message from client received
            enc_recv_data = sock.recv(2048)  # Should be ready to read
            if enc_recv_data:
                recv_data = crypto[sock].decrypt_msg_fernet(enc_recv_data)
                nonce_idx = recv_data.find(b'***NONCE***')
                if nonce_idx > 0:
                    nonce = recv_data[nonce_idx:recv_data.find(b'***END OF NONCE***') + len(b'***END OF NONCE***')]
                    if crypto[sock].validate_nonce(nonce):
                        recv_data = recv_data.replace(nonce, b'')
                    else:
                        del active_games[sock]
                        sel.unregister(sock)
                        sock.close()
                        raise OSError('Duplicate nonce received, closing connection: {}'.format(sock))

                messages = recv_data.split(EOM)
                if messages[-1] == b'' and len(messages) > 1:
                    messages = messages[:-1]
                for message in messages:
                    turn_taken = active_games[sock].shot_fired(message.decode('ascii'))
                    if message == b'BOARD':
                        # Next we encrypt the board using AES and send the encrypted baord to the client for safe
                        # keeping until the end of game where they will receive the key to check for cheating
                        enc_board, board_key, board_iv = crypto[sock].encrypt_board(active_games[sock].board)
                        board_key_iv[sock] = (board_key, board_iv)
                        token = crypto[sock].encrypt_msg_fernet(enc_board)
                        sock.sendall(token)
                        print("Board sent")
                    elif turn_taken:
                        token = crypto[sock].encrypt_msg_fernet(turn_taken.encode('ascii') + EOM + nonce)
                        sock.sendall(token)
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
                        del active_games[sock]
                        sel.unregister(sock)
                        sock.close()

            else:
                print('closing connection to', sock.getpeername(), flush=True)
                del active_games[sock]
                sel.unregister(sock)
                sock.close()
    elif active_games[sock].game_completed:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)
            dec_data = crypto[sock].decrypt_msg_fernet(recv_data)
            messages = dec_data.split(EOM)
            if messages[0] == b'BOARD KEY':
                token = crypto[sock].encrypt_msg_fernet(
                    board_key_iv[sock][0] + b'===END OF KEY===' + board_key_iv[sock][1] + b'===END OF IV===')
                sock.sendall(token)
                # print('Board key token: ',token)
                del active_games[sock]
                sel.unregister(sock)
                sock.close()
    else:
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(2048)
            dec_data = crypto[sock].decrypt_msg_rsa(recv_data)
            messages = dec_data.split(EOM)
            # print(messages)
            if messages[0] == b'START GAME':
                signeddh = crypto[sock].sign_dh_pubkey()
                sock.sendall(signeddh)
                # print('DH Key Sent: ',signeddh)
                # Had to add catching of non-blocking exception to cope
                # with the receiving of the client dh key
                try:
                    client_dh_key = sock.recv(2048)
                except BlockingIOError:
                    sock.setblocking(True)
                    client_dh_key = sock.recv(2048)
                    sock.setblocking(False)
                if client_dh_key.find(b'-----END PUBLIC KEY-----\n') < 0:
                    raise ValueError('Received Diffie-Hellman key is invalid')
                crypto[sock].setup_fernet(client_dh_key)
                token = crypto[sock].encrypt_msg_fernet(b'POSITIONING SHIPS' + EOM)
                sock.sendall(token)
                active_games[sock].setup_ship_placement()
                token = crypto[sock].encrypt_msg_fernet(b'SHIPS IN POSITION' + EOM)
                sock.sendall(token)
                active_games[sock].print_board()

            elif recv_data:
                print('Invalid command received. Closing connection: ', sock, flush=True)
                del active_games[sock]
                sel.unregister(sock)
                sock.close()
            else:
                print('Connection closed by client: ', sock.getpeername(), flush=True)
                del active_games[sock]
                sel.unregister(sock)
                sock.close()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # this block sets up the server socket and the callback for the sockets selector
    server_socket.bind((host, port))
    server_socket.setblocking(False)
    server_socket.listen()
    events = selectors.EVENT_READ
    sel.register(server_socket, events, accept_wrapper)
    while True:
        for key, mask in sel.select(timeout=None):
            callback = key.data
            callback(key, mask)
