# Classes for handling game logic. BattleShips is common game functionality
# between client and server. ClientGame is client specific methods and attributes
# ServerGame is server specific methods and attributes.

from game import BattleShips
import random
import numpy as np

class ServerGame(BattleShips):

    def __init__(self):
        super().__init__()
        self.initialised = False
        self.positioning = False

    def setup_ship_placement(self):   # randomly place ships on board
        self.initialised = True
        random.seed()
        orientations = ['V','H']
        for ship,length in self.ships:
            assigned=False
            while not assigned:
                row = random.choice(np.arange(0,len(self.rows),step=1))
                col = random.choice(np.arange(0,len(self.cols),step=1))
                orient = random.choice(orientations)
                try:
                    if orient=='H' and (col+length) <= 9:
                        if np.sum(self.board[row,col:col+length])==0:
                            self.board[row,col:col+length]=self.ships.index((ship,length))+1
                            assigned=True
                    elif orient=='V' and (row+length) <= 9:
                        if np.sum(self.board[row:row+length,col])==0:
                            self.board[row:row+length,col]=self.ships.index((ship,length))+1
                            assigned=True
                except IndexError as e:
                    pass
            self.running = True

    def shot_fired(self, coords):
        if self.validate_coords(coords):
            row = int(coords[1])-1
            col = self.cols.index(coords[0])
            self.turns_taken += 1
        else:
            return False

        if self.board[row,col] <= 0:
            self.board[row, col] = -1
            return 'MISS'
        elif self.board[row,col] > 0:
            self.board[row, col] = -2
            self.hit_count += 1
            if self.hit_count >= 14:
                self.running = False
            return 'HIT'
