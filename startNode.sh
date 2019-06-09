#!/usr/bin/env bash

wpython=`which python3`



if [ $# -gt 0 ]; then

    # developed using a virtual env so need to make distinction
    $wpython src/options_GUI.py $1


else
    $wpython src/options_GUI.py
fi