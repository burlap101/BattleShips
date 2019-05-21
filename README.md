# Battleships TCP Game COSC540

This is an interpretation of the classic battleships game.

## Author
Joe Crowley - Master of Computer Science Student
- UNE ID: 220202294
 

## Requirements

- Python version 3.6.7 or later including ```pip```
- Numpy version 1.16.2 

Use the package manager [pip3](https://pip.pypa.io/en/stable/) to install the following packages if not already.

```bash
pip3 install numpy==1.16.2
```

## Usage

To start a Battleships server, open a terminal and enter:
```bash
./startServer.sh [port]  
```
Optional port argument will listen for client connections on that port. 
If omitted then the server will listen on port 23456.  

To start a client, open another terminal or a terminal on another machine and enter:
```bash
./startClient.sh [host] [port]
```
None or both of the optional arguments must be specified for the client to execute. 
```host```  specifies the IP address or domain name of the battlehships server, which defaults to ```localhost``` (127.0.0.1), if omitted.
```port``` specifies the port that completes the TCP address for the listening socket of the server, which defaults to 23456 if omitted.

## Git Repo

[https://github.com/burlap101/COSC540-Assessment2.git](https://github.com/burlap101/COSC540-Assessment2.git)


.
