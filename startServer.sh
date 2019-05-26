#! /bin/bash

# if any arguments supplied will attempt to connect using them otherwise defaults are used from within the .py files.

if [ $# -gt 0 ]; then
  if [ $1 = "-h" ]; then
    cat docs/server_readme.txt
  else
    # developed using a virtual env so need to make distinction
    wpython=`which python3`
    $wpython src/server.py $1
  fi

else
  wpython=`which python3`
  $wpython src/server.py
fi
