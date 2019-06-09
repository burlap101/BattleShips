import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class CryptoCommon():
    # This class is parent to both server and client for the use of symmetric
    # encrypted communications using the Fernet (Encrypt-then-MAC) approach.
    TTL = 600  # 10 minutes after creation, a Fernet token expires.

    def __init__(self):
        print('Retrieving peer RSA public key')
        self.peer_rsa_pubkey = self.retrieve_peer_pubkey()
        print('Retrieving server RSA private key')
        self.rsa_privkey = self.retrieve_privkey()
        print('Completed')

    def retrieve_peer_pubkey(self):
        with open('.keys/bshipserverpub.pem', 'rb') as kf:
            peer_rsa_pubkey = serialization.load_pem_public_key(
                kf.read(),
                backend=default_backend()
            )
            return peer_rsa_pubkey

    def retrieve_privkey(self):
        # Retrieves the stored private RSA key for the server
        with open('.keys/bshipserverpriv.pem', 'rb') as kf:
            rsa_privkey = serialization.load_pem_private_key(
                kf.read(),
                password=None,
                backend=default_backend()
            )
            return rsa_privkey

    def decrypt_msg_rsa(self, ciphertext):
        # Decryption of messages for the starting of the game from the client. Uses padding and SHA-256 hash codes.
        message = self.rsa_privkey.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return message

    def encrypt_msg_rsa(self, message):
        ciphertext = self.peer_rsa_pubkey.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext


