#!/usr/bin/env bash

cd "$(dirname $(realpath $0))"

echo "Pulling changes"
git pull
source venv/bin/activate
echo "Reloading Eden Bot!..."
pkill python
nohup ./main.py &
echo "Eden bot has been reloaded!"
