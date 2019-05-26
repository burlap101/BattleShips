#! venv/bin/python3
#
# The ClientBackend class handles the socket and communication protocol, client side.
# In this application, an instance serves as an intermediate layer between the
# GUI and the client game object.
# Some of the methods are purely to return the state of the game to the GUI
# so the GUI doesn't interact with the game directly, and GUI mods are
# less likely to effect the comms and game functionality.
#

import socket

import cryptography.exceptions as crypt_exc
import numpy as np
from client_crypto import ClientCrypto
from client_game import ClientGame

EOM = b'\x0A'


class ClientBackend():

    def __init__(self, host='127.0.0.1', port=23456):
        self.crypto = ClientCrypto()  # handles all the encryption and decryption
        self.dh_key_verified = False
        self.host = host
        self.port = port
        self.s = self.socket_setup()
        self.enc_board = self.request_enc_board()
        self.game_completed = False
        if self.s:
            self.game = ClientGame()
        else:
            raise OSError('Something went wrong with establishing the game.')

    def socket_setup(self):
        # setup the TCP socket for communications
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
        s.connect((self.host, self.port))
        ciphertext = self.crypto.encrypt_msg_rsa(b'START GAME' + EOM)
        s.sendall(ciphertext)
        initialising = True
        while initialising:
            enc_response = s.recv(2048)  # retrieve characters from buffer
            if not self.dh_key_verified:
                try:
                    self.crypto.verify_server_dh_pubkey(enc_response)
                    s.sendall(self.crypto.dh_pubkey)
                    self.dh_key_verified = True
                except crypt_exc.InvalidSignature:
                    print('An invalid signature was detected from the server. Shutting down.', flush=True)
                    s.close()
                    return False
            else:
                response = self.crypto.decrypt_msg_fernet(enc_response)
                messages = response.split(EOM)
                if messages[-1] == b'' and len(messages) > 1:
                    messages = messages[:-1]  # last split will produce blank string need to filter out
                for message in messages:
                    print(message)
                    if message == b'SHIPS IN POSITION':
                        initialising = False
                    elif message == b'POSITIONING SHIPS':
                        pass
                    else:
                        print('There was an issue with the response from server. Shutting down.', flush=True)
                        s.close()
                        return False
        return s

    def take_shot(self, command):
        # This method takes the users chosen shot, validates, then sends and interprets the message received from
        # the server.

        if self.game.validate_coords(command.upper()):
            nonce = self.crypto.generate_nonce()
            message = command.upper().encode('ascii') + EOM + nonce
            token = self.crypto.encrypt_msg_fernet(message)
            self.s.sendall(token)
            enc_response = self.s.recv(2048)
            if not enc_response:  # empty data received means server closed connection
                self.s.close()
                raise OSError('Connection closed by server')
            response = self.crypto.decrypt_msg_fernet(enc_response)
            nonce_idx = response.find(nonce)
            if nonce_idx < 0:
                self.s.close()
                raise OSError('Invalid nonce received, closing connection.')
            response = response.replace(nonce, b'')  # Remove the nonce
            messages = response.split(EOM)  # Handle message normally.
            shots = []
            if len(messages) > 1 and messages[-1] == b'':  # get rid of blank list item due to split op.
                messages = messages[:-1]
            for message in messages:
                msg = message.decode('ascii')
                print(msg)
                shot = self.game.shot_fired(command.upper(), msg)
                if (not shot) and (self.game.hit_count != 14):
                    print('invalid protocol response received')
                    raise OSError
                elif self.game.hit_count == 14:
                    if msg == 'HIT':
                        enc_response = self.s.recv(2048)
                        response = self.crypto.decrypt_msg_fernet(enc_response)
                        stt = response.split(EOM)[-2]  # the server should have sent the amount of turns taken
                        shots.append(msg)
                        self.cheating_checks(int(stt))
                    elif int(msg):
                        self.cheating_checks(int(msg))
                    else:
                        raise OSError("There was an issue with the turns number sent from server.")
                else:
                    shots.append(msg)

            return [x for x in shots]

        else:
            return False

    def request_enc_board(self):
        token = self.crypto.encrypt_msg_fernet(b'BOARD' + EOM)
        self.s.sendall(token)
        enc_response = self.s.recv(2048)
        # print(enc_response)
        response = self.crypto.decrypt_msg_fernet(enc_response)
        if response.startswith(b'===START OF BOARD==='):
            enc_board = response.split(b'===END OF BOARD===')[0]
            return enc_board.replace(b'===START OF BOARD===', b'')
        else:
            self.s.close()
            raise OSError('There was an issue with the board sent. Shutting down.')

    def cheating_checks(self, server_turns_taken):
        # Contains all cheating checks to be performed at the end of the game
        # These include:
        # 1. Board tampering by server
        # 2. Turns mismatch between server and clients
        token = self.crypto.encrypt_msg_fernet(b'BOARD KEY' + EOM)
        self.s.sendall(token)
        enc_response = self.s.recv(2048)
        response = self.crypto.decrypt_msg_fernet(enc_response)
        splitted = response.split(b'===END OF KEY===')
        board_key = splitted[0]
        board_iv = splitted[1].split(b'===END OF IV===')[0]
        rows = self.crypto.decrypt_board(self.enc_board, board_key, board_iv)
        cheated = False
        self.cheating_message = ''
        for srow, crow in zip(rows, np.arange(0, self.game.num_rows, 1)):
            for snum, cnum in zip(srow, self.game.board[crow, :]):
                if (snum > 0) != (cnum == -2):
                    cheated = True
                    self.cheating_message += "Server board did not match your board."
        if server_turns_taken != self.game.turns_taken:
            cheated = True
            self.cheating_message += "Server turns did not match your turns."

        if cheated:
            print("Cheating was detected")
            self.cheating_message += "J'accuse the server is a cheater!"
            return self.cheating_message
        else:
            print("No cheating detected")
            self.cheating_message = "No cheating detected"
            return self.cheating_message

    # methods below serve as access points for GUI to retrieve ClientGame instance attributes and validate_coords method
    def get_board(self):
        return self.game.board

    def game_running(self):
        return self.game.running

    def get_moves(self):
        return self.game.turns_taken

    def get_hits(self):
        return self.game.hit_count

    def validate_coords_wrapper(self, coords):
        return self.game.validate_coords(coords)
