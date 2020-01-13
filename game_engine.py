import sys
import datetime as dt
import _thread as thread
from tkinter import *
from math import pi, sin, cos, e, sqrt, floor, ceil
from random import random, randint, choice
from time import perf_counter, sleep
from os import chdir
from pickle import *
import subprocess

clock = perf_counter

class Sound:

    CHUNK = 1024

    PA = pyaudio.PyAudio() 

    def __init__(sound, fname):
        sound.file = wave.open(fname, 'rb')

        sound.samplewidth = sound.file.getsamplewidth()

        sound.kwargs = {
            'format' : sound.PA.get_format_from_width(sound.samplewidth),
            'channels' : sound.file.getnchannels(),
            'rate' : sound.file.getframerate(),
            'output' : True,
        }

        sound.stream = sound.PA.open(**sound.kwargs)

        sound.on = False

    def play(sound):
        thread.start_new(sound.__play, ())

    def __play(sound):
        sound.on = True
        while sound.on and (data := sound.file.readframes(sound.CHUNK)):
            sound.stream.write(data)
        sound.stop()

    def stop(sound):
        sound.on = False
        sound.file.rewind()
    
    def close(sound):
        sound.stream.stop_stream()

## Get screen size
import pyautogui
w, h = pyautogui.size()