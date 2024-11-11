print('Starting RaspiLoopStation...','\n')
import jack
import pyaudio
import numpy as np
import time
import os
from gpiozero import LED, Button, LEDCharDisplay
from time import sleep

import logging
import mylib
logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename='RaspiLoopStation.log', level=logging.DEBUG)
    logger.info('Started')
    mylib.do_something()
    logger.info('Finished')

if __name__ == '__main__':
    main()

debounce_length = 0.1 #length in seconds of button debounce period
display = LEDCharDisplay(11, 25, 9, 10, 24, 22, 23, dp=27)
PLAYLEDR = (LED(26, active_high=False))
PLAYLEDG = (LED(20, active_high=False))
RECLEDR = (LED(0, active_high=False))
RECLEDG = (LED(1, active_high=False))
PLAYBUTTON = (Button(17, bounce_time = debounce_length))
RECBUTTON = (Button(18, bounce_time = debounce_length))
UNDOBUTTON = (Button(15, bounce_time = debounce_length))
PREVBUTTON = (Button(5, bounce_time = debounce_length))
NEXTBUTTON = (Button(12, bounce_time = debounce_length))
RESTARTBUTTON = (Button(6, bounce_time = debounce_length))
PLAYBUTTON.hold_time = 0.5

#get configuration (audio settings etc.) from file
settings_file = open('Config/settings.prt', 'r')
parameters = settings_file.readlines()
settings_file.close()

RATE = int(parameters[0]) #sample rate
CHUNK = 512 #int(parameters[1]) #buffer size
FORMAT = pyaudio.paInt16 #specifies bit depth (16-bit)
CHANNELS = 1 #mono audio
latency_in_milliseconds = int(parameters[2])
LATENCY = round((latency_in_milliseconds/1000) * (RATE/CHUNK)) #latency in buffers
INDEVICE = int(parameters[3]) #index (per pyaudio) of input device
OUTDEVICE = int(parameters[4]) #index of output device
overshoot_in_milliseconds = int(parameters[5]) #allowance in milliseconds for pressing 'stop recording' late
OVERSHOOT = round((overshoot_in_milliseconds/1000) * (RATE/CHUNK)) #allowance in buffers
MAXLENGTH = int(12582912 / CHUNK) #96mb of audio in total
SAMPLEMAX = 0.9 * (2**15) #maximum possible value for an audio sample (little bit of margin)
LENGTH = 0 #length of the first recording on track 1, all subsequent recordings quantized to a multiple of this.
LOOPNUMBER = int(0) #Pointer to the selected loop
setup_is_recording = False #set to True when track 1 recording button is first pressed
setup_donerecording = False #set to true when first track 1 recording is done
MODE = int(0)
PRESET = int (4)
finished = False
play_was_held = False
undo_was_held = False

#os.system ("sudo -H -u raspi killall fluidsynth")
print('Rate: ' + str(RATE) + ' / CHUNK: ' +  str(CHUNK),'\n')
print('Latency correction (buffers): ' + str(LATENCY),'\n')
print('Looking for devices','\n')
print('--- INDEVICE = ', str(INDEVICE),'\n')
print('--- OUTDEVICE = ', str(OUTDEVICE),'\n')

#UI do everything else

#Calling finish() will set finished flag, allowing program to break from loop at end of script and exit
def finish():
    finished = True

#Turn-Off all the Leds
def poweroffleds():
    RECLEDR.off()
    RECLEDG.off()
    PLAYLEDR.off()
    PLAYLEDG.off()

#restart_looper() restarts this python script
def restart_looper():
    global MODE
    global PRESET
    if MODE == 0:
        MODE = 1
        PRESET = 4
        #pa.terminate() #needed to free audio device for reuse
        poweroffleds()
        time.sleep(2)
        display.value = str(PRESET)
        cmd = "sudo -H -u raspi ./sf.sh"
        os.system (cmd)
        return
    if MODE == 1:
        MODE = 0
        time.sleep(2)
        os.system ("sudo -H -u raspi killall fluidsynth")
        os.execlp('python3', 'python3', 'RaspiLoopStation.py') #replaces current process with a new instance of the same script

def prevloop():
    global PRESET
    global LOOPNUMBER
    if MODE == 0 and setup_donerecording:
        if LOOPNUMBER == 0:
            LOOPNUMBER = 9
        else:
            LOOPNUMBER = LOOPNUMBER-1
        print('-= Last Loop =---> ', LOOPNUMBER,'\n')
    if MODE == 1:
        if PRESET >= 1:
            PRESET = PRESET-1
            display.value = (str(PRESET))[-1]
            f = open("./preset.sh", "w")
            f.write("echo 'prog 0 "+str(PRESET)+"' > /dev/tcp/localhost/9988")
            f.close()
            cmd = "sudo -H -u raspi bash ./preset.sh"
            print('----- Preset: ', str(PRESET),'\n')
            os.system (cmd)

def nextloop():
    global PRESET
    global LOOPNUMBER
    if MODE == 0 and setup_donerecording:
        if LOOPNUMBER == 9:
            LOOPNUMBER = 0
        else:
            LOOPNUMBER = LOOPNUMBER+1
        print('-= Next Loop =---> ', LOOPNUMBER,'\n')
    if MODE == 1:
        if PRESET <= 126:
            PRESET = PRESET+1
            display.value = (str(PRESET))[-1]
            f = open("./preset.sh", "w")
            f.write("echo 'prog 0 "+str(PRESET)+"' > /dev/tcp/localhost/9988")
            f.close()
            cmd = "sudo -H -u raspi bash ./preset.sh"
            print('----- Preset: ', str(PRESET),'\n')
            os.system (cmd)

def setrecord():
    global PRESET
    if MODE == 0:
        loops[LOOPNUMBER].set_recording()
    if MODE == 1:
        if PRESET >= 10:
            PRESET = PRESET-10
        changepreset()

def setmute():
    global PRESET
    global play_was_held
    if MODE == 0 and setup_donerecording:
        if not play_was_held:
            loops[LOOPNUMBER].toggle_mute()
        play_was_held = False
    if MODE == 1:
        if PRESET <= 110:
            PRESET = PRESET+10
        changepreset()

def setsolo():
    global play_was_held
    if MODE == 0 and setup_donerecording:
        play_was_held = True
        loops[LOOPNUMBER].toggle_solo()

def setclear():
    global undo_was_held
    if MODE == 0 and setup_donerecording:
        loops[LOOPNUMBER].clear()
        undo_was_held = False

def setundo():
    global undo_was_held
    if MODE == 0 and setup_donerecording:
        if not undo_was_held:
            undo_was_held = True
            loops[LOOPNUMBER].undo()

def changepreset():
    global PRESET
    display.value = (str(PRESET))[-1]
    f = open("./preset.sh", "w")
    f.write("echo 'prog 0 "+str(PRESET)+"' > /dev/tcp/localhost/9988")
    f.close()
    cmd = "sudo -H -u raspi bash ./preset.sh"
    print('----- Preset: ', str(PRESET),'\n')
    os.system (cmd)

#now defining functions of all the buttons during jam session...
PREVBUTTON.when_pressed = prevloop
PREVBUTTON.when_released = prevloop
NEXTBUTTON.when_pressed = nextloop
NEXTBUTTON.when_released = nextloop
RESTARTBUTTON.when_released = restart_looper
RESTARTBUTTON.when_pressed = restart_looper
RECBUTTON.when_pressed = setrecord
#RECBUTTON.when_held = setrecord
UNDOBUTTON.when_released = setundo
UNDOBUTTON.when_held = setclear
PLAYBUTTON.when_released = setmute
PLAYBUTTON.when_held = setsolo

#buffer to hold mixed audio from all 4 tracks
#play_buffer = np.zeros([CHUNK], dtype = np.int16)

#a buffer containing silence
#silence = np.zeros([CHUNK], dtype = np.int16)

#mixed output (sum of audio from tracks) is multiplied by output_volume before being played.
#This is updated dynamically as max peak in resultant audio changes
output_volume = np.float16(1.0)
#multiplying by up_ramp and down_ramp gives fade-in and fade-out
down_ramp = np.linspace(1, 0, CHUNK)
up_ramp = np.linspace(0, 1, CHUNK)
#fade_in() applies fade-in to a buffer
def fade_in(buffer):
    np.multiply(buffer, up_ramp, out = buffer, casting = 'unsafe')
#fade_out() applies fade-out to a buffer
def fade_out(buffer):
    np.multiply(buffer, down_ramp, out = buffer, casting = 'unsafe')

#pa = pyaudio.PyAudio()

class audioloop:
    def __init__(self):
        self.initialized = False
        self.length_factor = 1
        self.length = 0
        #self.main_audio and self.dub_audio contain audio data in arrays of CHUNKs.
        self.main_audio = np.zeros([MAXLENGTH, CHUNK], dtype = np.int16)
        #self.dub_audio contains the latest recorded dub. Clearing this achieves undo.
        self.dub_audio = np.zeros([MAXLENGTH, CHUNK], dtype = np.int16)
        self.readp = 0
        self.writep = 0
        self.is_recording = False
        self.is_playing = False
        self.is_waiting_play = False
        self.is_waiting_mute = False
        self.is_solo = False
        self.is_waiting = False
        self.pointer_last_buffer_recorded = 0 #index of last buffer added
        self.preceding_buffer = np.zeros([CHUNK], dtype = np.int16)
        """
        Dub ratio must be reduced with each overdub to keep all overdubs at the same level while preventing clipping.
        first overdub is attenuated by a factor of 0.9, second by 0.81, etc.
        each time the existing audio is attenuated by a factor of 0.9.
        """
        self.dub_ratio = 1.0

    #increment_pointers() increments pointers and, when restarting while recording, advances dub ratio
    def increment_pointers(self):
        if self.readp == self.length - 1:
            self.readp = 0
            if self.is_recording:
                self.dub_ratio = self.dub_ratio * 0.9
                print('Self dub ratio = ',self.dub_ratio,'\n')
        else:
            self.readp = self.readp + 1
        self.writep = (self.writep + 1) % self.length
        print('incrementing pointers')

    #initialize() raises self.length to closest integer multiple of LENGTH and initializes read and write pointers
    def initialize(self): #se inicializa cuando se termina de grabar la pista. No está inicializada después de hacer Clear.
        if self.initialized:
            print('     Redundant initialization.','\n')
            return
        self.writep = self.length - 1
        self.pointer_last_buffer_recorded = self.writep
        self.length_factor = (int((self.length - OVERSHOOT) / LENGTH) + 1)
        self.length = self.length_factor * LENGTH
        print('     length ' + str(self.length))
        print('     last buffer recorded ' + str(self.pointer_last_buffer_recorded))
        #crossfade
        fade_out(self.main_audio[self.pointer_last_buffer_recorded]) #fade out the last recorded buffer
        preceding_buffer_copy = np.copy(self.preceding_buffer)
        fade_in(preceding_buffer_copy)
        self.main_audio[self.length - 1, :] += preceding_buffer_copy[:]
        #audio should be written ahead of where it is being read from, to compensate for input+output latency
        self.readp = (self.writep + LATENCY) % self.length
        self.initialized = True
        self.is_playing = True
        self.increment_pointers()
        debug()

    #add_buffer() appends a new buffer unless loop is filled to MAXLENGTH
    #expected to only be called before initialization
    def add_buffer(self, data):
        if self.length >= (MAXLENGTH - 1):
            self.length = 0
            print('loop full')
            return
        self.main_audio[self.length, :] = np.copy(data) #Añade a main_audio el buffer q actualmente está entrando por PyAudio
        self.length = self.length + 1 #Incrementa el puntero de longitud del

    def toggle_mute(self):
        print('-=Toggle Mute=-','\n')
        if self.is_playing:
            self.is_waiting_mute = True
        else:
            self.is_waiting_play = True
            self.is_solo = False
        debug()

    def toggle_solo(self):
        print('-=Toggle Solo=-','\n')
        if not self.is_solo:
            print('-------------Solo')
            self.is_solo = True
            for i in range(9):
                if LOOPNUMBER != i and loops[i].initialized and not loops[i].is_solo and loops[i].is_playing:
                    loops[i].is_waiting_mute = True
        elif self.is_solo:
            print('-------------UnSolo')
            self.is_solo = False
            for i in range (9):
                if LOOPNUMBER != i and loops[i].initialized:
                    if not loops[i].is_playing:
                        loops[i].is_waiting_play = True
                    loops[i].is_solo = False
        self.is_waiting_play = True
        debug()

    #Restarting es True sólo si readp == 0 y la pista está inicializada, y sólo se comprueba cuando se termina de grabar la pista master (0)
    def is_restarting(self):
        #print('-= Is Restarting =-')
        if not self.initialized:
            return False
        if self.readp == 0:
            return True
        return False

    #read() reads and returns a buffer of audio from the loop
    #   if not initialized: Do nothing
    #   initialized but muted: Just increment pointers
    #   initialized and playing: Read audio from the loop and increment pointers
    def read(self):
        if not self.initialized:
            return(silence)

        if self.is_waiting_play and self.readp == 0:
            self.is_waiting_play = False
            self.is_playing = True

        if self.is_waiting_mute and self.readp == 0:
            self.is_waiting_mute = False
            self.is_playing = False


        if not self.is_playing or self.is_waiting_play:
            self.increment_pointers()
            return(silence)

        tmp = self.readp
        self.increment_pointers()

        if self.readp == 0:
            PLAYLEDR.on()
            PLAYLEDG.off()

        return(self.main_audio[tmp, :] + self.dub_audio[tmp, :])

    #dub() overdubs an incoming buffer of audio to the loop at writep
    #   at writep:
    #   first, the buffer from dub_audio is mixed into main_audio
    #   next, the buffer in dub_audio is overwritten with the incoming buffer
    def dub(self, data, fade_in = False, fade_out = False):
        if not self.initialized:
            return
        datadump = np.copy(data)
        self.main_audio[self.writep, :] = self.main_audio[self.writep, :] * 0.9 + self.dub_audio[self.writep, :] * self.dub_ratio
        self.dub_audio[self.writep, :] = datadump[:]

    #clear if muted, undo if playing.
    def clear_or_undo(self):
        print('-=Clear or Undo=-','\n')
        if self.is_recording:
            self.clear()
        if self.is_playing:
            self.undo()
        else:
            self.clear()

    #clear() clears the loop so that a new loop of the same or a different length can be recorded on the track
    def clear(self):
        global setup_donerecording
        global setup_is_recording
        global LENGTH
        print('-=Clear=-','\n')
        self.main_audio = np.zeros([MAXLENGTH, CHUNK], dtype = np.int16)
        self.dub_audio = np.zeros([MAXLENGTH, CHUNK], dtype = np.int16)
        self.initialized = False
        self.is_playing = False
        self.is_recording = False
        self.is_waiting = False
        self.length_factor = 1
        self.length = 0
        self.readp = 0
        self.writep = 0
        self.pointer_last_buffer_recorded = 0
        self.preceding_buffer = np.zeros([CHUNK], dtype = np.int16)
        if LOOPNUMBER == 0:
            for loop in loops:
                loop.is_waiting = False
                loop.is_recording = False
                loop.is_playing = False
                loop.initialized = False
                loop.length_factor = 1
                loop.length = 0
            setup_donerecording = False
            setup_is_recording = False
            LENGTH = 0
            print('-=Cleared ALL=-','\n')
        debug()

    #undo() resets dub_audio to silence
    def undo(self):
        print('-=Undo=-','\n')
        self.dub_audio = np.zeros([MAXLENGTH, CHUNK], dtype = np.int16)
        self.is_recording = False
        self.is_waiting = False
        debug()

    #start recording
    def start_recording(self, previous_buffer):
        print('-=Start Recording Track ', LOOPNUMBER,'\n')
        self.is_recording = True
        self.is_waiting = False
        self.preceding_buffer = np.copy(previous_buffer)

    #set_recording() either starts or stops recording
    #   if initialized and recording, stop recording (dubbing)
    #   if uninitialized and recording, stop recording (appending) and initialize
    #   if initialized and not recording, set as "waiting to record"
    def set_recording(self):
        global setup_is_recording
        global setup_donerecording
        print('----- set_recording called for Track', LOOPNUMBER,'\n')
        already_recording = False

        #if chosen track is currently recording, flag it
        if self.is_recording:
            already_recording = True
            #turn off recording
            if not self.initialized:
                self.initialize()
                if LOOPNUMBER == 0:
                    setup_is_recording = False
                    setup_donerecording = True
                    print('---Master Track Recorded---','\n')
        self.is_recording = False

        self.is_waiting = False
        #unless flagged, schedule recording. If chosen track was recording, then stop recording
        #like a toggle but with delayed enabling and instant disabling
        if not already_recording:
            if LOOPNUMBER == 0:
                self.is_recording = True
                setup_is_recording = True
            else:
                self.is_waiting = True
        debug()

#defining ten audio loops. loops[0] is the master loop.
#loops = (audioloop(), audioloop(), audioloop(), audioloop(), audioloop(), audioloop(), audioloop(), audioloop(), audioloop(), audioloop())
loops = [audioloop() for _ in range(10)]

def debug():
    print('  |init\t|isrec\t|iswait\t|isplay\t|iswaiP\t|iswaiM\t|Solo')
    print('0 |', int(loops[0].initialized), '\t|', int(loops[0].is_recording), '\t|', int(loops[0].is_waiting), '\t|', int(loops[0].is_playing), '\t|', int(loops[0].is_waiting_play), '\t|', int(loops[0].is_waiting_mute), '\t|', int(loops[0].is_solo))
    print('0 |', int(loops[1].initialized), '\t|', int(loops[1].is_recording), '\t|', int(loops[1].is_waiting), '\t|', int(loops[1].is_playing), '\t|', int(loops[1].is_waiting_play), '\t|', int(loops[1].is_waiting_mute), '\t|', int(loops[1].is_solo))
    print('0 |', int(loops[2].initialized), '\t|', int(loops[2].is_recording), '\t|', int(loops[2].is_waiting), '\t|', int(loops[2].is_playing), '\t|', int(loops[2].is_waiting_play), '\t|', int(loops[2].is_waiting_mute), '\t|', int(loops[2].is_solo))
    print('0 |', int(loops[3].initialized), '\t|', int(loops[3].is_recording), '\t|', int(loops[3].is_waiting), '\t|', int(loops[3].is_playing), '\t|', int(loops[3].is_waiting_play), '\t|', int(loops[3].is_waiting_mute), '\t|', int(loops[3].is_solo))
    print('setup_donerecording = ', setup_donerecording, ' setup_is_recording = ', setup_is_recording)
    print('length = ', loops[LOOPNUMBER].length, 'LENGTH = ', LENGTH, 'length_factor = ', loops[LOOPNUMBER].length_factor,'\n')

#update output volume to prevent mixing distortion due to sample overflow
#slow to run, so should be called on a different thread (e.g. a button callback function)
def update_volume(): #Not used
    print('---= Update Volume =---','\n')
    global output_volume
    peak = np.max(
        np.abs(
            loops[0].main_audio.astype(np.int32)[:][:]
            + loops[1].main_audio.astype(np.int32)[:][:]
            + loops[2].main_audio.astype(np.int32)[:][:]
            + loops[3].main_audio.astype(np.int32)[:][:]
            + loops[4].main_audio.astype(np.int32)[:][:]
            + loops[5].main_audio.astype(np.int32)[:][:]
            + loops[6].main_audio.astype(np.int32)[:][:]
            + loops[7].main_audio.astype(np.int32)[:][:]
            + loops[8].main_audio.astype(np.int32)[:][:]
            + loops[9].main_audio.astype(np.int32)[:][:]
            + loops[0].dub_audio.astype(np.int32)[:][:]
            + loops[1].dub_audio.astype(np.int32)[:][:]
            + loops[2].dub_audio.astype(np.int32)[:][:]
            + loops[3].dub_audio.astype(np.int32)[:][:]
            + loops[4].dub_audio.astype(np.int32)[:][:]
            + loops[5].dub_audio.astype(np.int32)[:][:]
            + loops[6].dub_audio.astype(np.int32)[:][:]
            + loops[7].dub_audio.astype(np.int32)[:][:]
            + loops[8].dub_audio.astype(np.int32)[:][:]
            + loops[9].dub_audio.astype(np.int32)[:][:]
        )
    )
    print('     peak = ' + str(peak))
    if peak > SAMPLEMAX:
        output_volume = SAMPLEMAX / peak
    else:
        output_volume = 1
    print(' --- output_volume = ' + str(output_volume))

#show_status() checks which loops are recording/playing and lights up LEDs accordingly
def show_status():
    display.value = str(LOOPNUMBER)

    if loops[LOOPNUMBER].is_recording:
        RECLEDR.on()
        RECLEDG.off()
    elif loops[LOOPNUMBER].is_waiting:
        RECLEDR.on()
        RECLEDG.on()
    elif setup_donerecording:
        RECLEDR.off()
        RECLEDG.off()

    if loops[LOOPNUMBER].is_waiting_play or loops[LOOPNUMBER].is_waiting_mute:
        PLAYLEDR.on()
        PLAYLEDG.on()
    elif loops[LOOPNUMBER].is_playing:
        PLAYLEDR.off()
        PLAYLEDG.on()
    else:
        PLAYLEDR.off()
        PLAYLEDG.off()

play_buffer = np.zeros([CHUNK], dtype = np.int16) #Buffer to hold mixed audio from all tracks
silence = np.zeros([CHUNK], dtype = np.int16) #A buffer containing silence
current_rec_buffer = np.zeros([CHUNK], dtype=np.int16) #Buffer to hold in_data
prev_rec_buffer = np.zeros([CHUNK], dtype = np.int16) #While looping, prev_rec_buffer keeps track of the audio buffer recorded before the current one

# Initializing JACK Client
client = jack.Client("RaspiLoopStation")
if client.status.server_started:
    print('----- JACK server started')

# Registering Ins/Outs Ports
input_port = client.inports.register("input_1")
print('----- Jack Client In Port Registered-----', str(input_port), '\n')

output_port = client.outports.register("output_1")
print('----- Jack Client Out Port Registered-----', str(output_port),'\n')

# Callback de procesamiento de audio
@client.set_process_callback
def looping_callback(frames):
    global play_buffer, current_rec_buffer, prev_rec_buffer
    global setup_donerecording, setup_is_recording
    global LENGTH

     # Read input buffer from JACK
    #in_data = input_port.get_array()[:].tobytes()
    current_rec_buffer[:] = np.right_shift(np.frombuffer(input_port.get_array()[:].tobytes(), dtype=np.int16), 1)

    # Setup: First Recording
    if not setup_donerecording: #if setup is not done i.e. if the master loop hasn't been recorded to yet
        RECLEDR.on()
        RECLEDG.on()
        PLAYLEDR.off()
        PLAYLEDG.off()

        if setup_is_recording: #if setup is currently recording, that recording action happens in the following lines
            RECLEDR.on()
            RECLEDG.off()
            PLAYLEDR.off()
            PLAYLEDG.off()

            if LENGTH >= MAXLENGTH: #if the max allowed loop length is exceeded, stop recording and start looping
                print('Overflow')
                setup_donerecording = True
                setup_is_recording = False
                return

            #otherwise append incoming audio to master loop, increment LENGTH and continue
            loops[0].add_buffer(current_rec_buffer)
            LENGTH += 1
            return silence
        #if setup not done and not currently happening then just wait
        else:
            return silence
    #execution ony reaches here if setup (first loop record and set LENGTH) finished.

    #when master loop restarts, start recording on any other tracks that are waiting
    if loops[0].is_restarting():
        #update_volume()
        for loop in loops:
            if loop.is_waiting:
                loop.start_recording(prev_rec_buffer)
                print('---=Recording Track number:', LOOPNUMBER, '=---','\n')

     #if master loop is waiting just start recording without checking restart
    if loops[0].is_waiting and not loops[0].initialized:
        loops[0].start_recording(prev_rec_buffer)
        print('????? if master loop is waiting just start recording without checking restart')

    #if a loop is recording, check initialization and accordingly append or overdub
        for loop in loops:
            if loop.is_recording:
                if loop.initialized:
                    print('------------------------------------------------=OverDub=-', end='\r')
                    loop.dub(current_rec_buffer)
                else:
                    print('------------------------------------------------=Append=-', end='\r')
                loop.add_buffer(current_rec_buffer)

    #add to play_buffer only one-fourth of each audio signal times the output_volume
    play_buffer[:] = np.multiply((
        loops[0].read().astype(np.int32)
        + loops[1].read().astype(np.int32)
        + loops[2].read().astype(np.int32)
        + loops[3].read().astype(np.int32)
        + loops[4].read().astype(np.int32)
        + loops[5].read().astype(np.int32)
        + loops[6].read().astype(np.int32)
        + loops[7].read().astype(np.int32)
        + loops[8].read().astype(np.int32)
        + loops[9].read().astype(np.int32)
    ), output_volume, out=None, casting='unsafe').astype(np.int16)

    #current buffer will serve as previous in next iteration
    prev_rec_buffer = np.copy(current_rec_buffer)

    #play mixed audio and move on to next iteration
    output_port.get_array()[:] = play_buffer[:]

#then we turn on all lights to indicate that looper is ready to start looping
print('----- Ready -----','\n')
RECLEDR.on()
RECLEDG.on()
PLAYLEDR.off()
PLAYLEDG.off()
debug()
#once all LEDs are on, we wait for the master loop record button to be pressed
print('---Waiting for Record Button---','\n')

@client.set_shutdown_callback
def shutdown(status, reason):
    print("JACK shutdown:", reason, status)

with client:
    capture = client.get_ports(is_physical=True, is_output=True)
    print(capture, '\n')
    if not capture:
        raise RuntimeError("No physical capture ports")

    for src, dest in zip(capture, client.inports):
        client.connect(src, dest)

    playback = client.get_ports(is_physical=True, is_input=True)
    print(playback, '\n')
    if not playback:
        raise RuntimeError("No physical playback ports")

    for src, dest in zip(client.outports, playback):
        client.connect(src, dest)

    print("Press Ctrl+C to stop")
    try:
        print("Pressssss")
        show_status()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
