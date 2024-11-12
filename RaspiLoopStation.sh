#!/bin/bash
killall fluidsynth
jack_control stop
killall jackd
sleep 2
jackd -d alsa -r 48000 -p 512 -n 2 -X raw -D -C hw:H5 -P hw:H5 &
#read -t 2 -p "I am going to wait for 2 seconds only ..."
cd ~/shared/RaspiLoopStation/
until python ./RaspiLoopStation.py
do
read -t 2 -p "I am going to wait for 2 seconds only ..."
done
