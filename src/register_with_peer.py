import socket, json, random
from crypto import CryptoCommon


EOM = b'\n'
class RegisterPeer():

    @staticmethod
    def register(host, port, s):
        message = (b'IDENTIFY' + EOM)
        s.sendall(message)
        resp = s.recv(1024)
        if resp.find(b'-----END PUBLIC KEY-----') < 0:
            print('No key was found in response')
            s.close()
            return False
        new_entry = {}
        with open('.keys/keylist.dat', 'r') as f:
            try:
                entries = json.load(f)
            except json.decoder.JSONDecodeError:
                entries = []
        for peer in entries:
            if peer['name'] == "{}:{}".format(host, port):
                entries.remove(peer)
        with open('.keys/keylist.dat', 'w') as f:
            new_entry['name'] = "{}:{}".format(host, port)
            new_entry['key'] = resp.decode()
            entries.append(new_entry)
            f.write(json.dumps(entries))

        crypto = CryptoCommon(host, port)
        crypto.initiate_rsa()
        with open('.keys/bshipserverpub.pem', 'rb') as f:
            server_pubkey = f.read()
        token = crypto.encrypt_msg_rsa(b'REGISTER' + EOM)
        s.sendall(token + server_pubkey)
        print('message sent: ', token + server_pubkey)
        return crypto

    @staticmethod
    def refresh_peers():
        # Refreshes the peer list before the game and returns a random choice for the game.

        with open('.keys/keylist.dat', 'r') as f:
            peer_list = json.load(f)
        for peer in peer_list:
            host, port = peer['name'].split(':')
            print(host, port)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
            try:
                s.connect((host, int(port)))
                RegisterPeer.register(host, int(port), s)
            except ConnectionRefusedError:
                print("Removing: ", peer['name'])
                peer_list.remove(peer)
            s.close()



        with open('.keys/keylist.dat', 'w') as f:
            f.write(json.dumps(peer_list))

        host, port = peer_list[random.randrange(len(peer_list))]['name'].split(':')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
        s.connect((host, int(port)))
        # now have to register the new socket with the chosen node.
        RegisterPeer.register(host, port, s)
        return s





