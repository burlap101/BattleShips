# The purpose of this file is to setup the client protocol for client cryptography.

import secrets

from crypto import CryptoCommon
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class ClientCrypto(CryptoCommon):

    def __init__(self):
        print('Retrieving server RSA public key')
        self.server_rsa_pubkey = self.retrieve_server_pubkey()
        print('Generating Diffie-Hellman key pair')
        self.dh_pubkey = self.generate_dh_keypair()
        print('Crypto initialising complete')
        self.current_nonce = self.generate_initial_nonce()
        self.nonces = [self.current_nonce]


    def retrieve_server_pubkey(self):
        with open('.keys/bshipserverpub.pem', 'rb') as kf:
            server_rsa_pubkey = serialization.load_pem_public_key(
                kf.read(),
                backend=default_backend()
            )
            return server_rsa_pubkey

    def encrypt_msg_rsa(self, message):
        ciphertext = self.server_rsa_pubkey.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def verify_server_dh_pubkey(self, signeddh):
        # the server has sent a Diffie-Hellman public key along with a signature
        # generated using the server's private RSA key using the DH key and hashed SHA-2.
        # This method now determines if the sent key was from the server by verifying the signature.
        # An InvalidSignature exception is raised if the verification fails
        server_dh_pubkey = signeddh[:signeddh.find(b'-----END PUBLIC KEY-----\n') + len(b'-----END PUBLIC KEY-----\n')]
        signature = signeddh[signeddh.find(b'-----END PUBLIC KEY-----\n') + len(b'-----END PUBLIC KEY-----\n'):]

        self.server_rsa_pubkey.verify(
            signature,
            server_dh_pubkey,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # if no exception raised then DH key is forwarded onto setup_fernet
        self.setup_fernet(server_dh_pubkey)

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



