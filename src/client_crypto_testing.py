from client_crypto import ClientCrypto
from cryptography.fernet import Fernet

print(Fernet.generate_key())

cc = ClientCrypto()
print(cc.generate_dh_keypair())
peer_key = cc.generate_dh_keypair()
print(peer_key)
cc.setup_fernet(peer_key)

while True:
    message = input('Type message to be encrypted: ')
    token = cc.encrypt_msg_fernet(message.encode('ascii'))
    ciphertext = cc.encrypt_msg_rsa(message.encode('ascii'))
    print("Fernet encryption: ", token)
    print("RSA Encryption: ", ciphertext)
    print(cc.decrypt_msg_fernet(token))
