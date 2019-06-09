#! venv/bin/python3
#
# Server protocol and socket handling. Allows for multiple clients
# with unique games to all play at once using selectors module and creating
# a new ServerGame instance.
# Achieved using selectors and non-blocking sockets (server doesn't 'hang' to wait for a response
# from the client instead polls all open sockets).

import selectors
import socket
import sys, json

from server_crypto import ServerCrypto
from server_game import ServerGame

sel = selectors.DefaultSelector()
# an empty dictionary to hold all game instances
active_games = {}
# an empty address to hold connection details currently registered.
peer_list = {}
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


def remove_all_associated_objects(sock):
    print("Sock: ", sock)
    print("Removing objects for ", sock.getpeername())
    if sock in active_games.keys():
        del active_games[sock]
    if sock in crypto.keys():
        del crypto[sock]
    sel.unregister(sock)
    sock.close()


def accept_wrapper(key, mask):
    # function for accepting all connections from hte clients
    sock = key.fileobj
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr, flush=True)
    conn.setblocking(False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, service_connection)
    print(conn.getpeername())
    crypto[conn] = ServerCrypto(conn.getpeername()[0], conn.getpeername()[1])

def service_connection(key, mask):
    # function services the connections using a series of conditional statements
    # and monitoring expected communications from the clients
    sock = key.fileobj
    out_msg = None
    if mask & selectors.EVENT_WRITE:
        if sock in active_games.keys():
            if active_games[sock].hit_count == 14 and active_games[sock].game_completed == False:
                # Encrypt prior to sending
                token = crypto[sock].encrypt_msg_rsa(str(active_games[sock].turns_taken).encode('ascii') + EOM)
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

    # all reading events dealt with here
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(2048)
        messages = [b"IGNOREME"]
        dec_data = b""
        print(recv_data)
        # IDENTIFY the only unencrypted message to be received.
        if recv_data.split(EOM)[0] == b'IDENTIFY':
            sock.setblocking(True)
            print(sock.getpeername())
            with open('.keys/bshipserverpub.pem') as f:
                pubkey = f.read()

            sock.sendall(pubkey.encode('ascii') + EOM)
            recv_data = sock.recv(2048)
            dec_data = crypto[sock].decrypt_msg_rsa(recv_data[:512])
            id_messages = dec_data.split(EOM)
            if id_messages[0] == b'REGISTER':
                print('Registering new key from peer')
                pubkey_loc = recv_data.find(b'-----BEGIN PUBLIC KEY-----')
                if pubkey_loc >= 0:
                    peer_pubkey = recv_data[pubkey_loc:]
                    with open('.keys/keylist.dat', 'r') as f:
                        try:
                            entries = json.load(f)
                        except json.decoder.JSONDecodeError:
                            entries = []
                    for peer in entries:
                        if peer['name'] == "{}:{}".format(sock.getpeername()[0],sock.getpeername()[1]):
                            entries.remove(peer)
                    with open('.keys/keylist.dat', 'w') as kl:
                        entries.append(dict([
                            ('name', "{}:{}".format(sock.getpeername()[0], sock.getpeername()[1])),
                            ('key', peer_pubkey.decode('ascii'))
                        ]))
                        kl.write(json.dumps(entries))
                    crypto[sock].initiate_rsa()
                    sock.setblocking(False)
                else:
                    print('Invalid key received. Closing connection: ', sock, flush=True)
                    sock.setblocking(False)
                    remove_all_associated_objects(sock)
            else:
                print('Invalid request sent. Peer not added to trusted list')
                sock.setblocking(False)
                remove_all_associated_objects(sock)

        elif recv_data:
            dec_data = crypto[sock].decrypt_msg_rsa(recv_data)
            messages = dec_data.split(EOM)

        else:
            print('Connection closed by client: ', sock.getpeername(), flush=True)
            remove_all_associated_objects(sock)

        print(messages)
        if messages[0] == b'START_GAME':
            # print('DH Key Sent: ',signeddh)
            # Had to add catching of non-blocking exception to cope
            # with the receiving of the client dh key
            active_games[sock] = ServerGame()  # create a unique game per connection
            token = crypto[sock].encrypt_msg_rsa(b'POSITIONING SHIPS' + EOM)
            sock.sendall(token)
            active_games[sock].setup_ship_placement()
            token = crypto[sock].encrypt_msg_rsa(b'SHIPS IN POSITION' + EOM)
            sock.sendall(token)
            active_games[sock].print_board()

        elif messages[0] == b'LIST_PEERS':
            with open('.keys/keylist.dat', 'r') as kl:
                peer_list = json.load(kl)
            for peer in peer_list:
                token = crypto[sock].encrypt_msg_rsa(peer['name'].encode('ascii') + EOM)
                sock.sendall(token + peer['key'])
            token = crypto[sock].encrypt_msg_rsa(b'END OF PEER LIST' + EOM)
            sock.sendall(token)
        elif messages[0] == b'':
            print('Connection closed by client: ', sock.getpeername())
            remove_all_associated_objects(sock)

        elif messages[0] == b'IGNOREME':
            pass

        elif sock in active_games.keys():
            if active_games[sock].running:
                nonce_idx = dec_data.find(b'***NONCE***')
                if nonce_idx > 0:
                    nonce = dec_data[nonce_idx:dec_data.find(b'***END OF NONCE***') + len(b'***END OF NONCE***')]
                    if crypto[sock].validate_nonce(nonce):
                        dec_data = dec_data.replace(nonce, b'')
                        messages = dec_data.split(EOM)
                    else:
                        remove_all_associated_objects(sock)
                        raise OSError('Duplicate nonce received, closing connection: {}'.format(sock))

                if messages[-1] == b'' and len(messages) > 1:
                    messages = messages[:-1]
                print(messages)
                for message in messages:
                    turn_taken = active_games[sock].shot_fired(message.decode())
                    if message == b'BOARD':
                        # Next we encrypt the board using AES and send the encrypted baord to the client for safe
                        # keeping until the end of game where they will receive the key to check for cheating
                        enc_board, board_key, board_iv = crypto[sock].encrypt_board(active_games[sock].board)
                        board_key_iv[sock] = (board_key, board_iv)
                        token = crypto[sock].encrypt_msg_rsa(enc_board)
                        sock.sendall(token)
                        print("Board sent")
                    elif turn_taken:
                        token = crypto[sock].encrypt_msg_rsa(turn_taken.encode('ascii') + EOM + nonce)
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
                        remove_all_associated_objects(sock)

            elif active_games[sock].game_completed and messages[0] != b"":
                if messages[0] == b'BOARD KEY':
                    sock.sendall(
                        board_key_iv[sock][0] + b'===END OF KEY===' + board_key_iv[sock][1] + b'===END OF IV==='
                    )
                    # print('Board key token: ',token)
                    remove_all_associated_objects(sock)
                else:
                    print('Invalid command received. Closing connection: ', sock, flush=True)
                    remove_all_associated_objects(sock)



with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # this block sets up the server socket and the callback for the sockets selector
    server_socket.bind((host, port))
    server_socket.setblocking(False)
    server_socket.listen(10)
    events = selectors.EVENT_READ
    sel.register(server_socket, events, accept_wrapper)
    while True:
        for key, mask in sel.select(timeout=None):
            callback = key.data
            callback(key, mask)
