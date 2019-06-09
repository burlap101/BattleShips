# The purpose of this file is to setup the client protocol for client cryptography.

import secrets

from crypto import CryptoCommon
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class ClientCrypto(CryptoCommon):

    def __init__(self):
        super().__init__()
        self.current_nonce = self.generate_initial_nonce()
        self.nonces = [self.current_nonce]

    def decrypt_board(self, enc_board, key, iv):
        # Method decrypts the supplied game board from server at the end of the
        # the game
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        byte_board = decryptor.update(enc_board)
        rows = byte_board.split(b'==')
        if rows[-1] == b'':
            rows = rows[:-1]
        return rows

    def generate_nonce(self):
        # Method generates the nonces. The nonce must be unique
        # for each turn and larger than the previous
        while True:
            increment = int.from_bytes(self.current_nonce, byteorder='big') + secrets.randbits(8)
            nonce = increment.to_bytes(8, byteorder='big')
            if (nonce not in self.nonces) and (nonce > max(self.nonces)):
                self.nonces.append(nonce)
                self.current_nonce = nonce
                return b'***NONCE***' + nonce + b'***END OF NONCE***'

    def validate_nonce(self, nonce):
        # Method validates received nonce from server matches the last generated
        nonce.replace(b'***NONCE***', b'')
        nonce.replace(b'***END OF NONCE***', b'')
        if self.current_nonce == nonce:
            return True
        else:
            return False

    def generate_initial_nonce(self):
        # Generates a nonce and ensures that the random increment wont cause an overflow
        # within 10,000 turns (a board of size 100x100 where largest random byte selected each time)
        while True:
            nonce = secrets.token_bytes(8)
            try:
                increment = (2550000+int.from_bytes(nonce, byteorder='big')).to_bytes(8, byteorder='big')
                if increment > nonce:
                    return nonce
            except OverflowError:
                print("Overflow on initial nonce possible, regenerating...")
                pass



