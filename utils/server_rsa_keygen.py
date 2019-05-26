import socket
import glob
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# generate a RSA key value pair if one does not exist already
# this is done the first time the server is to be deployed onto the server

def gen_keys():
    print('Generating server\'s RSA key pair...')
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    with open('.keys/bshipserverpriv.pem', 'wb') as privfile:
        privfile.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
            )
        )
    with open('.keys/bshipserverpub.pem', 'wb') as pubfile:
        pubfile.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
    print('Completed Successfully')

if os.path.exists('.keys'):
    gen_keys()

else:
    os.mkdir('.keys')
    gen_keys()
