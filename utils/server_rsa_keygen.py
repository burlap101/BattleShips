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

key_files = glob.glob('.keys/*')
if '.keys/bshipserverpriv.pem' in key_files:
    print('It appears an RSA key pair has already been created')
    try:
        with open(".keys/bshipserverpriv.pem", 'rb') as kf:
            private_key = serialization.load_pem_private_key(
                kf.read(),
                password=None,
                backend=default_backend()
            )
    except ValueError:
        print('There is a problem with the stored private key. Delete the file "keys/bshipserverpriv.pem" and run again to generate key pair')

elif os.path.exists('.keys'):
    gen_keys()

else:
    os.mkdir('.keys')
    gen_keys()
