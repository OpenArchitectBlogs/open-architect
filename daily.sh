#!/bin/bash

cd /root/open-architect
python3 engine.py >> logs/daily.log 2>&1
