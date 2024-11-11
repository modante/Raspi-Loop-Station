#!/bin/bash
killall fluidsynth
killall jackd
jack_control stop
sleep 1
#jackd -dalsa -r48000 -p512 -Xraw -D -Chw:H5 -Phw:H5 &
read -t 2 -p "I am going to wait for 2 seconds only ..."
cd ~/shared/RaspiLoopStation/
until python ./RaspiLoopStation.py
do
read -t 2 -p "I am going to wait for 2 seconds only ..."
done
