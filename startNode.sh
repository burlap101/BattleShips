#!/usr/bin/env bash

wpython=`which python3`
chmod +x *.sh

if [ -d ".keys" ]
then
    rm -r .keys/
fi

if [ $# -gt 0 ]; then
    $wpython utils/server_rsa_keygen.py
    $wpython src/options_GUI.py $1
else
    echo Error: A listening port must be provided
fi