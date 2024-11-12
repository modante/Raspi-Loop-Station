# Raspi-Loop-Station

This is a first version using Jack Client but still doesn't work: https://github.com/modante/Raspi-Loop-Station/tree/Jack-Implementation
There is a problem with buffers. I am not sure if the input buffer is been recorded on current_rec_buffer (line 540) or the play_buffer is been copied in the output_port.get_array() (line 616). The result is always silence.
Any help welcome :-)
