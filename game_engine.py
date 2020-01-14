import sys
import datetime as dt
import _thread as thread
import tkinter as tk

from math import pi, sin, cos, e, sqrt, floor, ceil
from random import random, randint, choice
from time import perf_counter, sleep
from pickle import *

import subprocess
import pyautogui

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
        sound.in_loop = False

        sound.open = True

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

    def loop(sound):
        if not sound.in_loop:
            thread.start_new(sound.__loop, ())

    def __loop(sound):
        sound.in_loop = True
        while sound.in_loop:
            sound.__play()
     
    def close(sound):
        if sound.in_loop: sound.in_loop = False
        if sound.on: sound.on = False
        
        sound.stream.stop_stream()
        sound.file.close()

        sound.open = False

## Get screen size
w, h = pyautogui.size()