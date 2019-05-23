from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
import base64


class CryptoCommon():
    # This class is parent to both server and client for the use of symmetric
    # encrypted communications using the Fernet (Encrypt-then-MAC) approach.
    TTL = 600  # 10 minutes after creation, a Fernet token expires.

    def generate_dh_keypair(self):
        # generates diffie hellman key pair for key exchange which will be used for the AES key during the game
        with open('.keys/dh_params.pem', 'rb') as param_file:
            parameters = serialization.load_pem_parameters(
                param_file.read(),
                backend=default_backend()
            )

        self.dh_private_key = parameters.generate_private_key()
        return self.dh_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def setup_fernet(self, peer_dh_pubkey):
        shared_key = self.dh_private_key.exchange(
            serialization.load_pem_public_key(
                peer_dh_pubkey,
                backend=default_backend()
            )
        )
        print('Shared key: ', shared_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
            backend=default_backend()
        ).derive(shared_key)
        print('Derived key: ', derived_key)
        fern_key = base64.urlsafe_b64encode(derived_key)
        print('Fernet key: ',fern_key)
        self.fern = Fernet(fern_key)

    def encrypt_msg_fernet(self, message):
        return self.fern.encrypt(message)

    def decrypt_msg_fernet(self, token):
        return self.fern.decrypt(token)     # TODO: insert ttl arg
