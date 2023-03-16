# Simple BCI backend for reading data. Does no filtering or classification.
#
# Created........: 28Feb2023 [ollie-d]
# Last Modified..: 16Mar2023 [ollie-d]

import pylsl
import time
import random
import collections

results_out = None
mrkstream_in = None
eeg_in = None

def lsl_mrk_outlet(name):
    info = pylsl.stream_info(name, 'Markers', 1, 0, pylsl.cf_string, 'ID66666666');
    outlet = pylsl.stream_outlet(info, 1, 1)
    print('backend.py created result outlet.')
    return outlet
    
def lsl_inlet(name):
    # Resolve all marker streams
    inlet = None
    tries = 0
    info = pylsl.resolve_stream('name', name)
    inlet = pylsl.stream_inlet(info[0], recover=False)
    print(f'backend.py has received the {info[0].type()} inlet.')
    return inlet
    
def main():
    terminate_backend = False
    store_data = False
    send_result = False
    
    # Wait for a marker, then start recording EEG data
    data = collections.deque() # fast datastructure for appending/popping in either direction
    
    print('main function started')
    while True and terminate_backend == False:
        # Constantly check for a marker
        mrk, t_mrk = mrkstream_in.pull_sample(timeout=0)
        eeg, t_eeg = eeg_in.pull_sample(timeout=0)

        # If we find a marker...
        if mrk is not None:
            print(f'{mrk[0]}')
            
            # ...either start saving data
            if mrk[0] in ('left', 'right'):
                store_data = True
                data = collections.deque() # reset the buffer
                
            # ...or stop and send result
            elif mrk[0] == 'blank':
                store_data = False
                send_result = True
                
            # ...or terminate the backend
            elif mrk[0] == 'die':
                store_data = False
                send_result = False
                terminate_backend = True
                # SAVE YOUR DATA HERE IF YOU CARE TO AND IF YOU SAVED YOUR BUFFERS
                print('Backend received die command; terminating.')
                
        if store_data and eeg is not None:
            data.append(eeg)

        elif send_result:
            send_result = False
            # do processing/classification here
            res = ['left', 'right'][random.randint(0, 1)] # inclusive

            # Wait 50ms then send a message (to give the task a chance to listen)
            time.sleep(0.05)
            print('Sent command')
            results_out.push_sample(pylsl.vectorstr([res]))
            
    
if __name__ == "__main__":
    # Initialize our streams
    random.seed()
    results_out = lsl_mrk_outlet('Result_Stream')
    mrkstream_in = lsl_inlet('Task_Markers')
    eeg_in = lsl_inlet('ollie_EEG')

    # Run out main function
    main()
