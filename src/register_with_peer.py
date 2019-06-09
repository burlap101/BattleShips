import socket, json

EOM = b'\n'
class RegisterPeer():

    @staticmethod
    def register(host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
        s.connect((host, port))
        message = (b'IDENTIFY' + EOM)
        s.sendall(message)
        resp = s.recv(1024)
        if resp.find(b'-----END PUBLIC KEY-----') < 0:
            return False
        current_entry = {}
        with open('.keys/keylist.dat', 'a') as f:
            current_entry['(\'{}\', {})'.format(host, port)] = resp.decode()
            f.write(json.dumps(current_entry))

        return True

