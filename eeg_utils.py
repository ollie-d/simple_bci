import numpy as np
import pyxdf
import re

def loadxdf(fname):
    '''Loads an XDF containing an EEG stream and marker stream

    Args:
        fname (str): Full file location of the XDF
        
    Returns:
        dict: Creates an EEG structure as a dict containing:
            eeg_data: Time series EEG data
            eeg_time: Time points corresponding to EEG data
            event_data: Marker data (asynchronous)
            event_time: Time points corresponding to marker onset
            channels: Electrode locations as a dict
            fs: Sampling rate of EEG data
            fs_i: Initial sampling rate of EEG data (will not change when resampling)
   
    Created:
        [ollie-d] 20May2019
    Last Modified:
        [ollie-d] 01Mar2023
    '''
    
    # Load dataset from xdf and export eeg_raw, eeg_time, mrk_raw, mrk_time, channels
    streams, fileheader = pyxdf.load_xdf(fname, dejitter_timestamps=False)
    
    # Create empty dict to be returned
    EEG = {}
    
    # Seperate streams
    eeg = None;
    mrk = None;
    for stream in streams:
        stream_type = stream['info']['type'][0]
        if stream_type.lower() == 'markers':
            mrk = stream
        if stream_type.lower() == 'eeg':
            eeg = stream
    if (eeg == None) or (mrk == None):
        print('ERROR, EEG AND MARKER STREAM NOT FOUND!')
        return
        
    # Create channel structure from stream info (if available)
    channel = {}
    num_chans = int(eeg['info']['channel_count'][0])
    try:
        desc = eeg['info']['desc'][0]['channels'][0]['channel']
        for i in range(num_chans):
            channel[desc[i]['label'][0]] = i
    except:
        print(f'WARNING: Data has {num_chans} channels, but no channel descriptions found. Creating generic channel info.')
        for i in range(num_chans):
            channel[f'Ch{i}'] = i
            
    # Let's also create time structures
    eeg_time = eeg['time_stamps']
    mrk_time = mrk['time_stamps']
    
    # Populate EEG with data
    EEG['eeg_data'] = eeg['time_series']
    EEG['eeg_time'] = eeg['time_stamps']
    EEG['event_data'] = mrk['time_series']
    EEG['event_time'] = mrk['time_stamps']
    EEG['channels'] = channel
    EEG['fs'] = int(eeg['info']['nominal_srate'][0])
    EEG['fs_i'] = int(eeg['info']['nominal_srate'][0]) # Note: This is a constant
    
    # Clear un-needed objects
    streams = None
    fileheader = None
    eeg = None
    mrk = None
    desc = None
    channel = None
    
    return EEG

def lsl_onsets(eeg_time, event_time):
    '''Searches for LSL marker onset times.
    
    A marker's onset time may not be perfectly aligned with the EEG timestamps.
    We therefore want to find the closest possible time which we can do
    by subtracting event times from the EEG and selecting the absolute min.
    
    Args:
        eeg_time (array): array of EEG times recorded from amplifier
        event_time (array): array of event times recorded from amplifier (asyncronous)
    
    Returns:
        An array of LSL onsets relative to eeg_time indices
    
    Created:
        [ollie-d] 31Jan2022
    Last Modified:
        [ollie-d] 01Mar2023
    '''
    
    output = [] # faster to append to list than pre-allocated np.zeros_like
    for i in range(len(event_time)):
        output.append(np.argmin(np.abs(eeg_time-event_time[i])))
        
    return np.array(output)
    
def epoch(EEG, epoch_s, epoch_e, event):
    '''Epochs continuous data using LSL EEG + event streams
    
    Args:
        EEG (dict): EEG data structuring containing EEG data+times and event data+times
        epoch_s (float): Time (in ms) that you want the epoch to start at
        epoch_e (float): Time (in ms) that you want the epoch to end at
        event (str): Value of event type you want to epoch to
    
    Returns:
        An ERP dict containing:
            bin_data: EEG data in epochs x samples x channels format
            bin_times: Time points corresponding to second dimension of bin_data
            events: Event markers (should all be of type event)
            fs: Sampling rate (in Hz)
            channels: Labels corresponding to 3rd dimension of bin_data
    
    Created:
        [ollie-d] 31Jan2022
    Last Modified:
        [ollie-d] 01Mar2023
    '''
    
    # Get marker onsets
    lsls = lsl_onsets(EEG['eeg_time'], EEG['event_time'])
    
    # Find locations of event in marker-index space
    mrks = list(np.array(EEG['event_data']).ravel()) # flatten list
    events_ix = [i for i, item in enumerate(mrks) if re.search(event, item)]

    # Use the marker-index space indices and lsls to get onset in EEG-index space
    onsets_ix = lsls[events_ix]
    
    # Translate epoch start/end into index space
    dt = 1000 / EEG['fs']
    s_ix = np.round(epoch_s / dt).astype(int)
    e_ix = np.round(epoch_e   / dt).astype(int)
    
    # Epoch should be epochs x samples x channels
    erp = np.zeros((len(onsets_ix), e_ix-s_ix, EEG['eeg_data'].shape[1]))
    for i in range(len(onsets_ix)):
        t0 = onsets_ix[i]
        try:
            erp[i, :, :] = EEG['eeg_data'][s_ix+t0:t0+e_ix, :]
        except ValueError:
            print(f'Warning: epoch {i} does not have the correct number of samples and cannot be epoched.')
        
    # Generate times and an ERP dict to return
    ERP = {'bin_data': erp,
           'bin_times': np.arange(epoch_s, epoch_e, (1000 / EEG['fs'])),
           'events': np.array(mrks)[events_ix],
           'fs': EEG['fs'],
           'channels': EEG['channels']}
    
    return ERP
