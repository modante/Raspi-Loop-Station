# Raspi-Loop-Station

Inspired on the great Raspi Looper from RandomVertebrate https://github.com/RandomVertebrate/raspi-looper

Main changes:
- New design from 8 buttons (Rec/Mute for each track) to 5 Buttons: Rec, Mute, Undo/Clear, Next Loop, Prev Loop.
  - Rec Button:
    - Press to Record. Press again to Stop Recording
  - Mute/Solo Button:
    - Press to Mute. Press again to UnMute
    - Hold to Solo. Hold again to UnSolo
  - Undo/Clear Button:
    - Press to Undo
    - Hold to Clear track (if track 0 is selected, Reset all the Looper)
  - Prev Button: Jumps to the prev track
  - Next Button: Jumps to the next track
- Support for 10 tracks (originally only 4)
- Mute/Solo waits till the starting of the Master Track to execute it

![imagen](https://github.com/user-attachments/assets/7e4a752f-1773-4dce-8de1-60d16994fe0f)

![imagen](https://github.com/user-attachments/assets/c0264a8e-3662-4eb9-855b-bd9bf15feecf)

ToDo:
- Adapt the code from PyAudio to Python Jack Client (https://jackclient-python.readthedocs.io/en/0.5.5/)
- Add FluidSynth to the Main program and connect it to the Looper
