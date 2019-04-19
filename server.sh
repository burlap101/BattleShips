#! /bin/bash

# if any arguments supplied will attempt to conenct using them otherwise defaults are used from within the .py files.

if [ $# -gt 0 ]; then
  if [ $1 = "-h" ]; then
    cat server_readme.txt
  else
    #developed using a virtual env so need to make distinction
    wpython=`which python3`
    $wpython server.py $1
  fi

else
  wpython=`which python3`
  $wpython server.py
fi
