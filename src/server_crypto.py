from crypto import CryptoCommon
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import numpy as np


class ServerCrypto(CryptoCommon):
    def __init__(self):
        print('Retrieving server RSA private key')
        self.rsa_privkey = self.retrieve_server_privkey()
        print('Generating Diffie-Hellman key pair')
        self.dh_pubkey = self.generate_dh_keypair()
        print('Crypto intialising complete')
        self.nonces = []

    def retrieve_server_privkey(self):
        with open('.keys/bshipserverpriv.pem', 'rb') as kf:
            rsa_privkey = serialization.load_pem_private_key(
                kf.read(),
                password=None,
                backend=default_backend()
            )
            return rsa_privkey

    def decrypt_msg_rsa(self, ciphertext):
        message = self.rsa_privkey.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return message

    def encrypt_board(self, board):
        # Function encrypts a byte representation of the board using
        # AES. It returns the encrypted board as well as the init vector
        # and key.
        byte_board = b''
        for row in np.arange(0,board.shape[0],1):
            row_buf=[]
            for space in np.nditer(board[row,:]):
                space = int(space)
                row_buf.append(space.to_bytes(1, byteorder='big', signed=True))
            byte_board += b''.join(row_buf) + b'=='    # append == to the end to show a new row when decrypting

        print(byte_board)
        key = os.urandom(32)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(byte_board)

        return b'===START OF BOARD==='+ ct + b"===END OF BOARD===", key, iv

    def sign_message(self, message):
        # Method creates a unique signature from the RSA private key for verification
        # by client.
        signature = self.rsa_privkey.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return signature

    def sign_dh_pubkey(self):
        # Uses the rsa private key to generate a signature based on the DH
        # public key and attaches it to the key for sending to the client
        signature = self.sign_message(self.dh_pubkey)

        return self.dh_pubkey+signature

    def validate_nonce(self, nonce):
        # method checks if received nonce is unique and stores it. 
        if nonce in self.nonces:
            return False
        else:
            self.nonces.append(nonce)
            return True
