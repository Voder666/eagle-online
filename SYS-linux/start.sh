#!/bin/bash

# 启动 lookupapi.py
python ascsac.py &

# # 等待一段时间，让 lookupapi.py 启动完成
sleep 5

# 启动 ascsac.py
python lookupapi.py
