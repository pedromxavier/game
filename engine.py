import sys
import datetime as dt
import _thread as thread
import tkinter as tk

from math import pi, sin, cos, e, sqrt, floor, ceil
from random import random, randint, choice
from time import perf_counter, sleep
from pickle import *
from PIL import Image, ImageTk

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

class BaseObject(object):
    """ BaseObject Args
        canvas : tk.Canvas object, where to draw this object.
        img : PIL.Image object
        x, y : int
    """
    def __init__(obj, canvas, img, x, y):
        obj.canvas = canvas
        
    @property
    def xy(obj):
        return obj.canvas.coords(obj.key)

    @property
    def x(obj):
        return obj.xy[0]
    
    @property
    def y(obj):
        return obj.xy[1]

class GameObject(BaseObject):
    """ Used to define a game object, such as spacecraft or meteors.
    """
    def __init__(obj, canvas, img, x, y):
        obj.canvas = canvas

        

        obj.map = Object.make_map(img)

        obj.key = obj.canvas.create_image(x, y, image)

    def __and__(A, B):
        """ Check collision between A and B:
            A & B -> {True, False}
        """
        ax, ay, aX, aY = A.box
        bx, by, bX, bY = B.box
        return not ((ax > bX or aX < bx) or (ay > bY or aY < by))
    
    @property
    def box(obj):
        """ (x_min, y_min, x_max, y_max)
        """
        x, y = obj.xy
        w, h = obj.w, obj.h
        return int(x-w/2), int(y-h/2), int(x+w/2), int(y+h/2)

class 

class GIF(list):
    
    def __init__(gif, game, fname, start, stop):
        buffer = [ImageTk(Image(fname % i)) for i in range(start, stop + 1)]
        list.__init__(gif, buffer)

        gif.canvas = game.canvas
        gif.lapse = game.GAME_LAPSE / 1_000

        gif.key = None

    def play(gif, x, y):
        thread.start_new(gif.__play, (x, y))

    def __play(gif, x, y):
        for frame in gif:
            gif.key = gif.canvas.create_image(x, y, image=frame)
            sleep(gif.lapse)
            gif.canvas.delete(gif.key)

    