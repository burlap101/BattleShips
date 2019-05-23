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
pip3 install cryptography==2.3
```

## Client Package Compilation

Since the game is now performed with encrypted communications as a key feature, a pair of RSA keys must be generated along with parameters for key exchange.  The compileGame.sh script handles this and needs to be run prior to starting a game (either client or server). The public RSA key, the Diffie-Hellman parameters and all files required are packaged to run a client from another host.:
```bash
./compileGame.sh
```
The resulting pacakage will be located in a file 'client.zip'.



## Usage

To start a Battleships server, open a terminal and enter:
```bash
./startServer.sh [port]  
```
Optional port argument will listen for client connections on that port.
If omitted then the server will listen on port 23456.  

To start a client, extract the client.zip package, created during the compilation step, open another terminal or a terminal on another machine and enter:
```bash
./startClient.sh [host] [port]
```
None or both of the optional arguments must be specified for the client to execute.
```host```  specifies the IP address or domain name of the battlehships server, which defaults to ```localhost``` (127.0.0.1), if omitted.
```port``` specifies the port that completes the TCP address for the listening socket of the server, which defaults to 23456 if omitted.

## Git Repo

[https://github.com/burlap101/COSC540-Assessment2.git](https://github.com/burlap101/COSC540-Assessment2.git)


.
