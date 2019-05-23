from crypto import CryptoCommon
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes



class ServerCrypto(CryptoCommon):
    def __init__(self):
        print('Retrieving server RSA private key')
        self.rsa_privkey = self.retrieve_server_privkey()
        print('Generating Diffie-Hellman key pair')
        self.dh_pubkey = self.generate_dh_keypair()
        print('Crypto intialising complete')

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

    def sign_dh_pubkey(self):
        # Uses the rsa private key to generate a signature based on the DH
        # public key and attaches it to the key for sending to the client
        signature = self.rsa_privkey.sign(
            self.dh_pubkey,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return self.dh_pubkey+signature
