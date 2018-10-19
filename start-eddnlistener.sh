#!/bin/sh

while :;
do
	./eddnlistener.py
	echo "EDDN listener died" | mail -s "EDDN listener died" athan
	sleep 10
done
