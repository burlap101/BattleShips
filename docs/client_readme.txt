usage: startClient.sh [host] [port]

[host] and [port] must both be specified if either to be used. If not supplied then default values used, which may not correspond to running server.

This is the client side of the battleship game. Script calls python script which then establishes connection to game server and sends START GAME. Once SHIP IN POSITION received from server then GUI opens up and play starts.
