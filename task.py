# Simplest BCI. Left/Right MI paradigm.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!! MAKE SURE refresh_rate IS SET TO YOUR MONITOR'S REFRESH RATE !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# Created........: 13Apr2021 [ollie-d]
# Last Modified..: 13Apr2021 [ollie-d]

import psychopy.visual
import psychopy.event
import time
import numpy as np
import pylsl
import random

# Global variables
win = None # Global variable for window (Initialized in main)
mrkstream_out = None # Global variable for LSL marker stream output (Initialized in main)
results_in = None # Global variable for LSL result input (Initialized in main)
fixation = None # Global variable for fixation cross (Initialized in main)
bg_color = [0, 0, 0]
win_w = 800#2560
win_h = 600#1440
refresh_rate = 165. # Monitor refresh rate (CRITICAL FOR TIMING)


#========================================================
# High Level Functions
#========================================================
def Paradigm(num_trials=1):
    terminate = False
    # Iterate through sequence and perform:
    # 1000ms direction text (no fixation)
    # 500ms  blank screen
    # 3000ms fixation only <-- doing MI
    # 500ms  blank screen
    # 1000ms classification result
    # 1000ms blank screen
    
    # Initialize fixation cross
    fixation = psychopy.visual.ShapeStim(
                win=win,
                units='pix',
                size = 50,
                fillColor=[1, 1, 1],
                lineColor=[1, 1, 1],
                lineWidth = 1,
                vertices = 'cross',
                name = 'off', # Used to determine state
                pos = [0, 0]
            )
            
    # Initialize text (for instructions & results)
    text = psychopy.visual.TextStim(win,
                    'TEST TEXT', font='Open Sans', units='pix', 
                    pos=(0,0), alignText='center',
                    height=36, color=[1, 1, 1]
                    )
    
    for i in range(num_trials):
        # Randomly determine if trial will be left or right
        trial = ['left', 'right'][random.randint(0, 1)] # inclusive
        
        # 1000 ms direction instruction
        text.text = trial
        for frame in range(MsToFrames(1000, refresh_rate)):
            text.draw()
            win.flip()
            
        # 500ms blank screen
        for frame in range(MsToFrames(500, refresh_rate)):
            win.flip()
    
        # 3000ms fixation cross (send LSL marker here)
        for frame in range(MsToFrames(3000, refresh_rate)):
            # Send LSL marker on first frame
            if frame == 0:
                mrkstream_out.push_sample(pylsl.vectorstr([trial]))
            fixation.draw()
            win.flip()
            
        # 500ms blank screen
        for frame in range(MsToFrames(500, refresh_rate)):
            win.flip()
        
        # ~1000ms classification result
        # If you wanted to be precise, store the time at the start
        # then get it once marker is received and subtract that
        # from 1000ms. Note that the best you can do is still a single
        # frame and likely you'll get a result within that time.
        # For this example we'll just assume we don't care.
       
        # Flip screen and send blank
        win.flip()
        mrkstream_out.push_sample(pylsl.vectorstr(['blank']))
       
        # Wait until we get a valid result from the backend
        results = None
        print('Looking for result')
        while results is None and terminate == False:
            results, t = results_in.pull_sample(timeout=0)  
            if terminate:
                break
        
        # Once results found, display them
        text.text = f'Classifier returned: {results[0]}'
        print(f'{text.text}')
        for frame in range(MsToFrames(1000, refresh_rate)):
            text.draw()
            win.flip()
        
        # 1000ms blank screen
        for frame in range(MsToFrames(1000, refresh_rate)):
            win.flip()

def MsToFrames(ms, fs):
    dt = 1000 / fs;
    return np.round(ms / dt).astype(int);

def lsl_mrk_outlet(name):
    info = pylsl.stream_info(name, 'Markers', 1, 0, pylsl.cf_string, 'ID0123456789');
    outlet = pylsl.stream_outlet(info, 1, 1)
    print('task.py created outlet.')
    return outlet
    
def lsl_inlet(name):
    # Resolve all marker streams
    inlet = None
    tries = 0
    info = pylsl.resolve_stream('name', name)
    inlet = pylsl.stream_inlet(info[0], recover=False)
    print(f'task.py has received the {info[0].type()} inlet.')
    return inlet

if __name__ == "__main__":
    # Set random seed
    random.seed()
    
    # Initialize LSL marker streams
    mrkstream_out = lsl_mrk_outlet('Task_Markers') # important this is first
    results_in = lsl_inlet('Result_Stream')

    # Create PsychoPy window
    win = psychopy.visual.Window(
        screen = 0,
        size=[win_w, win_h],
        units="pix",
        fullscr=False,
        color=bg_color,
        gammaErrorPolicy = "ignore"
    )
    
    # Wait a second for the streams to settle down
    time.sleep(1)
    
    # Run through paradigm
    Paradigm(4)
    