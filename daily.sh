#!/bin/bash

cd /root/open-architect
source venv/bin/activate
python3 engine.py >> logs/daily.log 2>&1
