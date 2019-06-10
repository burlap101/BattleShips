import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class CryptoCommon():
    # This class is parent to both server and client for the use of symmetric
    # encrypted communications using the Fernet (Encrypt-then-MAC) approach.
    TTL = 600  # 10 minutes after creation, a Fernet token expires.

    def __init__(self):
        print('Retrieving server RSA private key')
        self.rsa_privkey = self.retrieve_privkey()
        print('Completed')
        self.peer_rsa_pubkey = None

    def initiate_rsa(self, node_name):
        print("Initiating RSA...")
        self.peer_rsa_pubkey = self.retrieve_peer_pubkey(node_name)
        print("Done", self.peer_rsa_pubkey)

    def retrieve_peer_pubkey(self, node_name):
        with open('.keys/keylist.dat', 'r') as f:
            entries = json.load(f)
        print("searching for: ", node_name)
        for entry in entries:
            print(entry['name'])
            if entry['name'] == node_name:
                peer_rsa_pubkey = serialization.load_pem_public_key(
                entry['key'].encode('ascii'),
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



