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

EOM = b'\x0A'

class Listener():

    def __init__(self, port):
        self.sel = selectors.DefaultSelector()
        # an empty dictionary to hold all game instances
        self.active_games = {}
        # an empty address to hold connection details currently registered.
        self.peer_list = {}
        # an empty dictionary to manage all per connection specific encryption
        self.crypto = {}

        # an empty dictionary to hold the key and iv for decryption of the board by the client after completion
        self.board_key_iv = {}
        self.host = ''
        self.port = port
        self.close_flag = False

    def begin_selector(self):
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # this block sets up the server socket and the callback for the sockets selector
            self.server_socket.bind((self.host, self.port))
            self.server_socket.setblocking(False)
            self.server_socket.listen(10)
            events = selectors.EVENT_READ
            self.sel.register(self.server_socket, events, self.accept_wrapper)
            while True:
                for key, mask in self.sel.select(timeout=None):
                    callback = key.data
                    callback(key, mask)


    def remove_all_associated_objects(self, sock):
        print("Sock: ", sock)
        print("Removing objects for ", sock.getpeername())
        if sock in self.active_games.keys():
            del self.active_games[sock]
        if sock in self.crypto.keys():
            del self.crypto[sock]
        self.sel.unregister(sock)
        sock.close()

    def accept_wrapper(self, key, mask):
        # function for accepting all connections from hte clients
        sock = key.fileobj
        conn, addr = sock.accept()  # Should be ready
        print('accepted', conn, 'from', addr, flush=True)
        conn.setblocking(False)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, self.service_connection)
        print(conn.getpeername())
        self.crypto[conn] = ServerCrypto()

    def service_connection(self, key, mask):
        # function services the connections using a series of conditional statements
        # and monitoring expected communications from the clients
        sock = key.fileobj
        out_msg = None
        if mask & selectors.EVENT_WRITE:
            if sock in self.active_games.keys():
                if self.active_games[sock].hit_count == 14 and self.active_games[sock].game_completed == False:
                    # Encrypt prior to sending
                    token = self.crypto[sock].encrypt_msg_rsa(str(self.active_games[sock].turns_taken).encode('ascii') + EOM)
                    sock.sendall(token)
                    print(
                        "Game with ",
                        sock.getpeername(),
                        " finished in ",
                        self.active_games[sock].turns_taken,
                        " moves",
                        flush=True
                    )
                    self.active_games[sock].running = False
                    self.active_games[sock].game_completed = True

        # all reading events dealt with here
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(2048)
            messages = [b"IGNOREME"]
            dec_data = b""
            #print(recv_data)
            # IDENTIFY the only unencrypted message to be received.
            if recv_data.split(EOM)[0] == b'IDENTIFY':
                sock.setblocking(True)
                print(sock.getpeername())
                with open('.keys/bshipserverpub.pem') as f:
                    pubkey = f.read()

                sock.sendall(pubkey.encode('ascii') + EOM)
                recv_data = sock.recv(2048)
                dec_data = self.crypto[sock].decrypt_msg_rsa(recv_data[:512])
                id_messages = dec_data.split(EOM)
                if id_messages[0] == b'REGISTER':
                    print('Registering new key from peer')
                    pubkey_loc = recv_data.find(b'-----BEGIN PUBLIC KEY-----')
                    if pubkey_loc >= 0:
                        peer_pubkey = recv_data[pubkey_loc:]
                        node_name = id_messages[1].decode('ascii')
                        print("\n\n******NODE NAME: ", node_name)
                        with open('.keys/keylist.dat', 'r') as f:
                            try:
                                entries = json.load(f)
                            except json.decoder.JSONDecodeError:
                                entries = []
                        for peer in entries:
                            if peer['name'] == node_name:
                                entries.remove(peer)
                        with open('.keys/keylist.dat', 'w') as kl:
                            entries.append(dict([
                                ('name', node_name),
                                ('key', peer_pubkey.decode('ascii'))
                            ]))
                            kl.write(json.dumps(entries))
                        self.crypto[sock].initiate_rsa(node_name)
                        sock.setblocking(False)
                    else:
                        print('Invalid key received. Closing connection: ', sock, flush=True)
                        sock.setblocking(False)
                        self.remove_all_associated_objects(sock)
                else:
                    print('Invalid request sent. Peer not added to trusted list')
                    sock.setblocking(False)
                    self.remove_all_associated_objects(sock)

            elif recv_data:
                dec_data = self.crypto[sock].decrypt_msg_rsa(recv_data)
                messages = dec_data.split(EOM)

            else:
                print('Connection closed by client: ', sock.getpeername(), flush=True)
                self.remove_all_associated_objects(sock)

            #print(messages)
            if messages[0] == b'START_GAME':
                # print('DH Key Sent: ',signeddh)
                # Had to add catching of non-blocking exception to cope
                # with the receiving of the client dh key
                self.active_games[sock] = ServerGame()  # create a unique game per connection
                token = self.crypto[sock].encrypt_msg_rsa(b'POSITIONING SHIPS' + EOM)
                sock.sendall(token)
                self.active_games[sock].setup_ship_placement()
                token = self.crypto[sock].encrypt_msg_rsa(b'SHIPS IN POSITION' + EOM)
                sock.sendall(token)
                self.active_games[sock].print_board()

            elif messages[0] == b'LIST_PEERS':
                with open('.keys/keylist.dat', 'r') as kl:
                    peer_list = json.load(kl)
                for peer in peer_list:
                    print("**********************SENDING***************")
                    print("Name: ", peer['name'])
                    # print("Key: ", peer['key'])
                    token = self.crypto[sock].encrypt_msg_rsa(peer['name'].encode('ascii') + EOM)
                    sock.sendall(token + peer['key'].encode('ascii'))

                token = self.crypto[sock].encrypt_msg_rsa(b'END OF PEER LIST' + EOM)
                sock.sendall(token)
            elif messages[0] == b'':
                print('Connection closed by client: ', sock.getpeername())
                self.remove_all_associated_objects(sock)

            elif messages[0] == b'IGNOREME':
                pass

            elif sock in self.active_games.keys():
                if self.active_games[sock].running:
                    nonce_idx = dec_data.find(b'***NONCE***')
                    if nonce_idx > 0:
                        nonce = dec_data[nonce_idx:dec_data.find(b'***END OF NONCE***') + len(b'***END OF NONCE***')]
                        if self.crypto[sock].validate_nonce(nonce):
                            dec_data = dec_data.replace(nonce, b'')
                            messages = dec_data.split(EOM)
                        else:
                            self.remove_all_associated_objects(sock)
                            raise OSError('Duplicate nonce received, closing connection: {}'.format(sock))

                    if messages[-1] == b'' and len(messages) > 1:
                        messages = messages[:-1]
                    print(messages)
                    for message in messages:
                        turn_taken = self.active_games[sock].shot_fired(message.decode())
                        if message == b'BOARD':
                            # Next we encrypt the board using AES and send the encrypted baord to the client for safe
                            # keeping until the end of game where they will receive the key to check for cheating
                            enc_board, board_key, board_iv = self.crypto[sock].encrypt_board(self.active_games[sock].board)
                            self.board_key_iv[sock] = (board_key, board_iv)
                            token = self.crypto[sock].encrypt_msg_rsa(enc_board)
                            sock.sendall(token)
                            print("Board sent")
                        elif turn_taken:
                            token = self.crypto[sock].encrypt_msg_rsa(turn_taken.encode('ascii') + EOM + nonce)
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
                            self.remove_all_associated_objects(sock)

                elif self.active_games[sock].game_completed and messages[0] != b"":
                    if messages[0] == b'BOARD KEY':
                        sock.sendall(
                            self.board_key_iv[sock][0] + b'===END OF KEY===' + self.board_key_iv[sock][1] + b'===END OF IV==='
                        )
                        # print('Board key token: ',token)
                        self.remove_all_associated_objects(sock)
                    else:
                        print('Invalid command received. Closing connection: ', sock, flush=True)
                        self.remove_all_associated_objects(sock)

    def close_listener(self):
        self.server_socket.close()




