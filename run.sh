#!/bin/bash

dev_id=""
if [ "$1" == "client1" ]; then
    dev_id="id:e6614864d30b7b36"
elif [ "$1" == "client2" ]; then
    dev_id="id:e6614864d3467534"
elif [ "$1" == "client3" ]; then
    dev_id="id:e6614864d34a5c34"
elif [ "$1" == "client4" ]; then
    dev_id="id:e661640843438724"
else
    exit 1;
fi

python3 ../tools/update_urls.py
mpremote connect $dev_id mip install file:. 
mpremote connect $dev_id run mahjong2040/__init__.py