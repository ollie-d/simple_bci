# Simple BCI

This repo contains code for two things:

## 1. Simple skeleton for a BCI using LSL + PsychoPy
No actual EEG processing or ML is involved in this example.

Simply create a virtual environment and conda install psychopy and pip install pylsl.

Create an EEG LSL stream with the specified name using the OpenBCI GUI (or any other means).

Demo/mini lecture found here: https://youtu.be/UWEngkRzFCE

## 2. Simple skeleton for using pyxdf to load in/epoch XDF files
No filtering is done in this example.

You can integrate multiple LSL streams using the LabRecorder which saves data into .xdf files.

This utilizes `pyxdf`. There is a jupyter notebook which walks through analysis of a synthetic dataset.
