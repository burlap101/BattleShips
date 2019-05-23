#! venv/bin/python3
# File used for testing protocol either client or server side.
# Command line interaction only. Supply one or two args to pose as server
# or client respectively. Set up other side with corresponding recipient. 
#
#
#

import socket
import sys

client = False
host = ''
if len(sys.argv) > 2:
    host = sys.argv[1]
    port = int(sys.argv[2])
    client = True
else:
    port = int(sys.argv[1])

EOM = b'\n'
running = True
initialised = False
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    if client:
        s.connect((host, port))
        while running:
            msg = input(">>>")
            s.sendall(msg.encode('ascii')+EOM)
            while not initialised:
                response = s.recv(1024)
                if not response:
                    print('Connection closed by server')
                    running = False
                    s.close()
                    break
                print(response.decode('ascii'))
                if response.split(b'\n')[-2]==b'SHIPS IN POSITION':
                    initialised = True
                if not initialised:
                    retry = input('Wait for more responses (y/n)?: ')
                    if retry != 'y':
                        break
    else:
        s.bind((host,port))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print(conn.getpeername(), 'connected')
            response = conn.recv(1024)
            print(response.decode('ascii'))
            msg = input('>>>')
            conn.sendall(msg.encode('ascii')+EOM)
            msg = input('>>>')
            conn.sendall(msg.encode('ascii')+EOM)
            while running:
                response = conn.recv(1024)
                if not response:
                    print('Connection closed by client')
                    running = False
                    conn.close()
                    break
                print(response.decode('ascii'))
                msg = input('>>>')
                conn.sendall(msg.encode('ascii')+EOM)
