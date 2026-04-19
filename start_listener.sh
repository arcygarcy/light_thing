#!/bin/bash
# Move to the directory where the python script actually lives
cd /home/pi/code/light_thing/listener

# Ensure dependencies are installed
/home/pi/code/light_thing/listener/venv/bin/pip install -r requirements.txt

# Use the correct path to the venv inside the listener folder
/home/pi/code/light_thing/listener/venv/bin/python3 /home/pi/code/light_thing/listener/listener.py