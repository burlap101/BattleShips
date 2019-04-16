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
from game import ClientGame
import game

EOM = b'\x0A'

class ClientBackend():

    def __init__(self, host='127.0.0.1', port=23456):
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
        s.sendall('START GAME'.encode('ascii')+EOM)
        intialising = True
        while intialising:
            response = s.recv(1024)  # retrieve characters from buffer
            messages = response.split(EOM)
            if messages[-1] == b'' and len(messages)>1:
                messages = messages[:-1]  # last split will produce blank string need to filter out
            for message in messages:
                msg = message.decode('ascii')
                print(msg)
                if msg=='SHIPS IN POSITION':    # only accept two messages at start of game
                    intialising = False
                elif msg=='POSITIONING SHIPS':
                    pass
                else:
                    print('There was an issue with the response from server. Shutting down.')
                    s.close()
                    return False
        return s

    def take_shot(self, command):
        if self.game._validate_coords(command.upper()):
            bytes_sent = self.s.send(command.upper().encode('ascii')+EOM)
            if bytes_sent==len(command)+1:
                response = self.s.recv(1024)
                if not response:        # empty data received means server closed connection
                    print('connection closed by server')
                    self.s.close()
                    raise OSError
                messages = response.split(EOM)
                for message in messages:
                    msg = message.decode('ascii')
                    shot = self.game.shot_fired(command.upper(), msg)
                    if not shot and self.game.hit_count!=14:
                        raise ValueError
                    print(msg)
                    return msg
        else:
            return False

    def get_board(self):
        return self.game.board

    def game_running(self):
        return self.game.running

    def get_moves(self):
        return self.game.turns_taken

    def validate_coords(self, coords):
        return self.game._validate_coords(coords)
