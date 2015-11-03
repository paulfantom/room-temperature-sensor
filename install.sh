#!/bin/bash

sudo apt-get install -y python-virtualenv python-smbus

virtualenv venv
source venv/bin/activate
pip install paho-mqtt
