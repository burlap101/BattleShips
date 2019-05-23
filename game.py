# Classes for handling game logic. BattleShips is common game functionality
# between client and server. ClientGame is client specific methods and attributes
# ServerGame is server specific methods and attributes.

import numpy as np
import random
import sys


class BattleShips():
    # Class and common methods between the client and server for game functionality

    def __init__(self, rows=9, columns=9):
        # Could expand the board if desired by entering arguments at object instantiation
        self.ships = [
            ('A',2),
            ('L',3),
            ('H',4),
            ('C',5),
        ]   # list of tuples to represent the ships.

        alphabet = 'abcdefghijklmnopqrstuvwxyz'.upper()
        self.cols = alphabet[:columns]
        self.rows = [x for x in range(rows+1)]
        self.board = np.zeros((rows, columns))
        self.running = False
        self.hit_count = 0
        self.turns_taken = 0

    def print_board(self, file=sys.stdout):
        row_buf = [x for x in self.cols]
        print(' ',' '.join(row_buf), file=file, flush=True)
        for row in np.arange(0,9,1):
            row_buf=[]
            for space in np.nditer(self.board[row,:]):
                space = int(space)
                if space==0:
                    row_buf.append('.')
                elif space > 0:
                    row_buf.append(self.ships[space-1][0])
                elif space == -1:
                    row_buf.append('O')
                elif space == -2:
                    row_buf.append('X')

            print(row+1, ' '.join(row_buf), file=file, flush=True)

    def validate_coords(self, coords):
        try:
            if (coords[0] in self.cols) and (int(coords[1:])-1 in self.rows):
                return True
            else:
                return False
        except (ValueError, IndexError):
            return False
