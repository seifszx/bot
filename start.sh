#!/bin/bash
Xvfb :99 -screen 0 1280x800x24 &
export DISPLAY=:99
sleep 2
python main.py
