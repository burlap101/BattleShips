#! /usr/bin/python3

import socket


host = '129.180.124.29'
port = 23456

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print('attempting to connect')
    s.connect((host,port))
    print('connected to ',host)
    s.sendall('START GAME'.encode('ascii'))

    response = s.recv(1024)
    print(response.decode('ascii'))
    response = s.recv(1024)
    print(response.decode('ascii'))
    test = response=='SHIPS IN POSITION'
    while True:
        command = input()
        bytes_sent = s.send(command.encode('ascii'))
        if bytes_sent==len(command):
            response = s.recv(1024)
            if not response:
                print('connection closed by server')
                break
            response = response.decode('ascii')
            print(response)







