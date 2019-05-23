#! /bin/bash

# if any arguments supplied will attempt to connect using them otherwise defaults are used from within the .py files.
if [ $# -gt 1 ]; then
  ping=`ping -c 1 $1 | grep bytes | wc -l`
  if [ $ping -gt 1 ]; then
    # developed using a virtualenv so need to make distinction
    wpython=`which python3`
    $wpython src/GUI.py $1 $2
  else
    echo "Bad hostname supplied"
  fi

elif [ $# -gt 0 ]; then
  if [ $1 = "-h" ]; then
    cat docs/client_readme.txt
  else
    echo "Supply host and port as separate arguments (i.e. with a space between each)"
  fi

else
  wpython=`which python3`
  $wpython src/GUI.py
fi
