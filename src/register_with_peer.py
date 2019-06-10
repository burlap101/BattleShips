import socket, json, random
from crypto import CryptoCommon


EOM = b'\n'
class RegisterPeer():

    @staticmethod
    def register(host, port, s, node_name):
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

        crypto = CryptoCommon()
        crypto.initiate_rsa("{}:{}".format(host, port))
        with open('.keys/bshipserverpub.pem', 'rb') as f:
            server_pubkey = f.read()
        token = crypto.encrypt_msg_rsa(b'REGISTER' + EOM + node_name.encode('ascii') + EOM)
        s.sendall(token + server_pubkey)
        # print('message sent: ', token + server_pubkey)
        return crypto

    @staticmethod
    def refresh_peers(node_name):
        # Refreshes the peer list before the game and returns a random choice for the game.

        with open('.keys/keylist.dat', 'r') as f:
            peer_list = json.load(f)

        # remove this node from peer list
        for peer in peer_list:
            if peer['name'] == node_name:
                peer_list.remove(peer)

        # this loop refreshes and checks the current list of nodes
        for peer in peer_list:
            host, port = peer['name'].split(':')
            print(host, port)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
            try:
                s.connect((host, int(port)))
                crypto = RegisterPeer.register(host, int(port), s, node_name)
            except ConnectionRefusedError:
                print("Removing: ", peer['name'])
                peer_list.remove(peer)
            s.close()

        # this loop does initial retrieve of the peers' lists
        known_names = [x['name'] for x in peer_list]
        new_peers = []
        for peer in peer_list:
            host, port = peer['name'].split(':')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
            try:
                s.connect((host, int(port)))
                crypto = RegisterPeer.register(host, int(port), s, node_name)
                token = crypto.encrypt_msg_rsa(b'LIST_PEERS' + EOM)
                s.sendall(token)
                while True:
                    enc_resp = s.recv(2048)
                    print("RESPONSE LENGTH: ", len(enc_resp))
                    if len(enc_resp) > 512:
                        response = crypto.decrypt_msg_rsa(enc_resp[:512])
                    else:
                        response = crypto.decrypt_msg_rsa(enc_resp)
                    messages = response.split(EOM)
                    if messages[0] == b'END OF PEER LIST':
                        break
                    elif messages[0] == b'':
                        raise ConnectionRefusedError
                    elif messages[0].decode('ascii') in known_names:
                        pass
                    elif messages[0].decode('ascii') == node_name:
                        print("\n%%%%%%%%%%%%%%%%%%%Own entry FOUND%%%%%%%%%%%%%%%%%%%\n")
                        pass
                    else:
                        print('adding to known peers: ', messages[0])
                        known_names.append(messages[0])
                        key_start = enc_resp.find(b'-----BEGIN PUBLIC KEY-----')
                        new_key = enc_resp[key_start:].decode('ascii')
                        new_peers.append(dict([('name', messages[0].decode('ascii')), ('key', new_key)]))
            except ConnectionRefusedError:
                print("Removing: ", peer['name'])
                peer_list.remove(peer)
            s.close()
        print("^^^^^^^NEW PEER LIST: ", new_peers)
        # this loop keeps iterating until all nodes are known
        while len(new_peers) > 0:
            peer = new_peers.pop()
            host, port = peer['name'].split(':')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
            try:
                s.connect((host, int(port)))
                known_names.append("{}:{}".format(s.getsockname()[0], s.getsockname()[1]))
                crypto = RegisterPeer.register(host, int(port), s, node_name)
                token = crypto.encrypt_msg_rsa(b'LIST_PEERS' + EOM)
                s.sendall(token)
                while True:
                    enc_resp = s.recv(2048)
                    if len(enc_resp) > 512:
                        response = crypto.decrypt_msg_rsa(enc_resp[:512])
                    else:
                        response = crypto.decrypt_msg_rsa(enc_resp)
                    messages = response.split(EOM)
                    if messages[0] == b'END OF PEER LIST':
                        break
                    elif messages[0] == b'':
                        raise ConnectionRefusedError
                    elif messages[0] in known_names:
                        pass
                    elif messages[0].decode('ascii') == node_name:
                        print("\n*************Own entry FOUND***********\n")
                        pass
                    else:
                        print('adding to known peers: ', messages[0])
                        known_names.append(messages[0])
                        key_start = enc_resp.find(b'-----BEGIN PUBLIC KEY-----')
                        new_key = enc_resp[key_start:].decode('ascii')
                        new_peers.append(dict([('name', messages[0].decode('ascii')), ('key', new_key)]))
            except ConnectionRefusedError:
                print("Removing: ", peer['name'])
                peer_list.remove(peer)

            print("+++++CURRENT PEER: ", peer['name'])
            if peer in new_peers:
                new_peers.remove(peer)
            if peer not in peer_list:
                peer_list.append(peer)
            s.close()

        # what we are left with is a list of all known nodes on the network and their keys
        with open('.keys/keylist.dat', 'w') as f:
            f.write(json.dumps(peer_list))

        host, port = peer_list[random.randrange(len(peer_list))]['name'].split(':')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
        s.connect((host, int(port)))
        # now have to register the new socket with the chosen node.
        RegisterPeer.register(host, port, s, node_name)
        return s





