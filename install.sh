#!/bin/bash

sudo apt-get install -y python-virtualenv

virtualenv venv
source venv/bin/activate
pip install paho-mqtt smbus-cffi
exit 0
