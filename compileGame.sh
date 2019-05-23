#! /bin/bash

wpython=`which python3`
$wpython utils/server_rsa_keygen.py
echo Generating Diffie-Hellman parameters
$wpython utils/generate_dh_params.py
packaged=`ls -a -p | grep ClientPackage/ | wc -w`
echo Completed

if [ $packaged -eq 0 ]; then
  mkdir ClientPackage
  mkdir ClientPackage/.keys/
  mkdir ClientPackage/src/
  mkdir ClientPackage/docs/
  cp .keys/bshipserverpub.pem ClientPackage/.keys/
  cp .keys/dh_params.pem ClientPackage/.keys/
  cp startClient.sh ClientPackage/
  cp src/client_game.py ClientPackage/src/
  cp docs/client_readme.txt ClientPackage/docs/
  cp src/GUI.py ClientPackage/src/
  cp src/game.py ClientPackage/src/
  cp docs/battleship.png ClientPackage/docs/
  cp src/client_crypto.py ClientPackage/src/
  cp README.md ClientPackage/
  zip -r client.zip ClientPackage/*
  rm -r ClientPackage/
  echo
  echo Client package client.zip created. Extract on client host and follow instructions within README.md to begin game with the corresponding server.

else
  echo It appears ClientPackage has already been created. Delete this directory if recompiling.
fi
