#!/bin/bash

if [ $(id -u) -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

eval $SUDO apt-get install -yqq python-virtualenv

virtualenv venv
source venv/bin/activate
pip install paho-mqtt smbus-cffi
exit 0
