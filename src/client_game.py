# Classes for handling game logic. BattleShips is common game functionality
# between client and server. ClientGame is client specific methods and attributes
# ServerGame is server specific methods and attributes.

from game import BattleShips


class ClientGame(BattleShips):

    def __init__(self):
        super().__init__()
        self.running = True

    # this method validates response from server and updates board client side.
    def shot_fired(self, coords, result):
        if self.validate_coords(coords):
            row = int(coords[1]) - 1
            col = self.cols.index(coords[0])
            self.turns_taken += 1
        else:
            return False

        if result[:4] == 'MISS' and self.board[row, col] == 0:
            self.board[row, col] = -1
        elif result[:3] == 'HIT' and self.board[row, col] == 0:
            self.board[row, col] = -2
            self.hit_count += 1
            if self.hit_count >= 14:
                self.running = False

        return True
