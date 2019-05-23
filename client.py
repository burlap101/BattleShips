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
from client_crypto import ClientCrypto
from client_game import ClientGame
import cryptography.exceptions as crypt_exc
import game
import secrets

EOM = b'\x0A'

class ClientBackend():

    def __init__(self, host='127.0.0.1', port=23456):
        self.crypto = ClientCrypto()
        self.dh_key_verified = False
        self.host=host
        self.port=port
        self.s = self.socket_setup()
        if self.s:
            self.game = ClientGame()
        else:
            raise OSError

    def socket_setup(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
        s.connect((self.host, self.port))
        ciphertext=self.crypto.encrypt_msg_rsa(b'START GAME'+EOM)
        s.sendall(ciphertext)
        intialising = True
        while intialising:
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
                print(enc_response)
                response = self.crypto.decrypt_msg_fernet(enc_response)
                messages = response.split(EOM)
                if messages[-1] == b'' and len(messages)>1:
                    messages = messages[:-1]  # last split will produce blank string need to filter out
                for message in messages:
                    msg = message.decode('ascii')
                    if msg=='SHIPS IN POSITION':    # only accept two messages at start of game
                        intialising = False
                    elif msg=='POSITIONING SHIPS':
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
            token = self.crypto.encrypt_msg_fernet(command.upper().encode('ascii')+EOM)
            self.s.sendall(token)
            enc_response = self.s.recv(2048)
            if not enc_response:        # empty data received means server closed connection
                print('connection closed by server', flush=True)
                self.s.close()
                raise OSError
            response = self.crypto.decrypt_msg_fernet(enc_response)
            messages = response.split(EOM)
            shots = []
            if len(messages)>1 and messages[-1]==b'':  # get rid of blank list item due to split op.
                messages = messages[:-1]
            for message in messages:
                msg = message.decode('ascii')
                print(msg)
                shot = self.game.shot_fired(command.upper(), msg)
                if (not shot) and (self.game.hit_count!=14):
                    print('invalid protocol response received')
                    raise OSError
                elif self.game.hit_count == 14:
                    try:  # Have two shots at waiting for turns value to come through.
                        if int(message) == self.game.turns_taken:
                            shots.append(msg)      # Error checking returned value
                        else:
                            print("There was a mismatch between server and client turns recorded")
                            raise OSError
                    except ValueError:
                        enc_response = self.s.recv(2048)
                        response = self.crypto.decrypt_msg_fernet(enc_response)
                        stt = response.split(EOM)[-2]   # the server should have sent the amount of turns taken
                        if int(stt.decode('ascii')) == self.game.turns_taken:
                            shots.append(msg)
                        else:
                            print("There was a mismatch between server and client turns recorded")
                            raise OSError
                else:
                    shots.append(msg)

            return [x for x in shots]

        else:
            return False

    # methods below serve as access points for GUI to retrieve ClientGame instance attributes and validate_coords method
    def get_board(self):
        return self.game.board

    def game_running(self):
        return self.game.running

    def get_moves(self):
        return self.game.turns_taken

    def get_hits(self):
        return self.game.hit_count

    def validate_coords(self, coords):
        return self.game.validate_coords(coords)
