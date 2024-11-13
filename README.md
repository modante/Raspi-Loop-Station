# Raspi-Loop-Station

This is a first version using Jack Client.

FluidSynth is also working together simultaneously with the looper:
- When MODEBUTTON is pressed, the PREV and NEXT Buttons changes to the Prev/Next Preset of FluidSynth
- while the REC/MUTE/UNDO Buttons allows to Rec, Mute/Solo, Undo/Clear of the selected Track, allowing to record de Output L/R of FluidSynth on the selected Track of Looper.

-----
Inspired on the great Raspi Looper from RandomVertebrate https://github.com/RandomVertebrate/raspi-looper

Main changes:
- New design from 8 buttons (Rec/Mute for each track) to 6 Buttons: Rec, Mute, Undo/Clear, Next Loop, Prev Loop and Mode.
  - **Mode Button:** Switches from Looper Mode to FluidSynth Mode.
  - **Rec Button:**
    - Press to Record. Press again to Stop Recording (Looper Mode) / Decrease 10 preset numbers (FluidSynth Mode)
  - **Mute/Solo Button:**
    - Press to Mute. Press again to UnMute (Looper Mode) / Increase 10 preset numbers (FluidSynth Mode)
    - Hold to Solo. Hold again to UnSolo
  - **Undo/Clear Button:**
    - Press to Undo
    - Hold to Clear track (if track 0 is selected, Reset all the Looper)
  - **Prev Button:** Jumps to the prev track (Looper Mode) / Decrease 1 preset number (FluidSynth Mode)
  - **Next Button:** Jumps to the next track (Looper Mode) / Increase 1 preset number (FluidSynth Mode)
- Added a 7 segments display to show the Track number (0-9) (Looper Mode) or the last digit of GM selected preset (when FluidSynth Mode)
- Support for 10 tracks (originally only 4) and could be increased till the limits of resources/latency.
- Mute/Solo waits till the starting of the Master Track to execute it

![imagen](https://github.com/user-attachments/assets/7e4a752f-1773-4dce-8de1-60d16994fe0f)

![imagen](https://github.com/user-attachments/assets/c0264a8e-3662-4eb9-855b-bd9bf15feecf)


