#! /bin/bash

wpython=`which python3`
$wpython utils/server_rsa_keygen.py
$wpython utils/generate_dh_params.py
packaged=`ls -a -p | grep ClientPackage/ | wc -w`

if [ $packaged -eq 0 ]; then
  mkdir ClientPackage
  mkdir ClientPackage/.keys/
  cp .keys/bshipserverpub.pem ClientPackage/.keys/
  cp .keys/dh_params.pem ClientPackage/.keys/
  cp startClient.sh ClientPackage/
  cp client_game.py ClientPackage/
  cp client_readme.txt ClientPackage/
  cp GUI.py ClientPackage/
  cp game.py ClientPackage/
  cp battleship.png ClientPackage/
  cp client_crypto.py ClientPackage/
  cp README.md ClientPackage/
  zip client.zip ClientPackage/*
  rm -r ClientPackage/

else
  echo It appears ClientPackage has already been created. Delete .keys directory if recompiling.
fi
