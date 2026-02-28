#!/bin/bash

cd /root/open-architect
source venv/bin/activate
pip install -r requirements.txt
python3 engine.py >> logs/daily.log 2>&1
