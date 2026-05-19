#!/bin/sh
#rm -rf /cover/*
/csms > server.log 2>&1 &
sleep 1
tail -f server.log