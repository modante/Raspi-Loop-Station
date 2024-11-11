#!/bin/bash
killall fluidsynth
sleep 3
fluidsynth -is -a alsa -o audio.alsa.device="hw:4" -g 0.9 -o "shell.port=9988" -f /home/raspi/shared/RaspiLoopStation/sf.conf /usr/share/sounds/sf2/FluidR3_GM.sf2 &
#fluidsynth -ifs -a jack -g 0.9 -o "shell.port=9988" -f /home/raspi/shared/raspi-looper/sf.conf /usr/share/sounds/sf2/FluidR3_GM.sf2 &
sleep 3
aconnect 28:0 128:0
exit


