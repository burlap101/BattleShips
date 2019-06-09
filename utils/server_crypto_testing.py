from server_crypto import ServerCrypto
from client_crypto import ClientCrypto

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

sc = ServerCrypto()
signeddh = sc.sign_dh_pubkey()
print(signeddh)
signature = signeddh[signeddh.find(b'-----END PUBLIC KEY-----\n')+len(b'-----END PUBLIC KEY-----\n'):]
scdh = signeddh[:signeddh.find(b'-----END PUBLIC KEY-----\n')+len(b'-----END PUBLIC KEY-----\n')]
print(signature)
print(scdh)

cc = ClientCrypto()
cc.verify_server_dh_pubkey(signeddh)
message=b'START_GAME'
encm = cc.encrypt_msg_rsa(message)
print(encm)
decm = sc.decrypt_msg_rsa(encm)
print(decm)
print(scdh==sc.dh_pubkey)

shared_key = sc.dh_private_key.exchange(cc.dh_private_key.public_key())
same_shared_key = cc.dh_private_key.exchange(sc.dh_private_key.public_key())

print(shared_key==same_shared_key)

# cc.setup_fernet(peer_key)

# while True:
#     message = input('Type message to be encrypted: ')
#     token = cc.encrypt_msg_fernet(message.encode('ascii'))
#     ciphertext = cc.encrypt_msg_rsa(message.encode('ascii'))
#     print("Fernet encryption: ", token)
#     print("RSA Encryption: ", ciphertext)
#     print(cc.decrypt_msg_fernet(token))
