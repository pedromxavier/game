import datetime as dt
import _thread as thread
import tkinter as tk
import numpy as np

from math import pi, sin, cos, e, sqrt, floor, ceil
from random import random, randint, choice

from time import perf_counter as clock
from time import sleep

from PIL import Image, ImageTk

import sys
import os
import pickle
import subprocess
import pyautogui
import pyaudio
import wave

class Sound:

    CHUNK = 1024

    PA = pyaudio.PyAudio() 

    def __init__(sound, fname):
        try:
            sound.file = wave.open(fname, 'rb')
        except wave.Error:
            sound.file = Sound.fix_wav(fname)

        sound.samplewidth = sound.file.getsampwidth()

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

    @staticmethod
    def fix_wav(fname):
        import librosa
        import soundfile

        head, tail = os.path.split(fname)

        temp_fname = os.path.join(head, "temp_{}".format(tail))

        try:
            return wave.open(temp_fname, 'rb')
        except FileNotFoundError:
            data, junk = librosa.load(fname, sr=16000)
            soundfile.write(temp_fname, data, sr=16000)

            return wave.open(temp_fname, 'rb')


class BaseObject(object):
    """ BaseObject Args
        canvas : tk.Canvas object, where to draw this object.
        img : PIL.Image object
        x, y : int
    """
    def __init__(obj, canvas, img, x, y, dx=0, dy=0):
        obj.canvas = canvas

        obj.dxdy = dx, dy

    def move(obj):
        obj.canvas.move(obj.key, *obj.dxdy)
        
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
        canvas : tk.Canvas object
        img : PIL.Image object
        x, y : int
    """
    __groups__ = []

    def __init__(obj, canvas, img, x, y):
        obj.canvas = canvas

        obj.img = img

        obj.tkimg = ImageTk(obj.img)

        obj.map = GameObject.make_map(obj.img)

        obj.key = obj.canvas.create_image(x, y, image=obj.tkimg)

    @staticmethod
    def make_map(img):
        array = np.array(img)

    @staticmethod
    def box_intersection(A, B):
        """ Check collision between A and B:
            A & B -> {True, False}
        """
        ax, ay, aX, aY = A.box
        bx, by, bX, bY = B.box

        cx = max(ax, bx)
        cX = min(aX, bX)

        cy = max(ay, by)
        cY = min(aY, bY)

        if cx > cX or cy > cY :
            return None
        else:
            return (cx, cy, cX, cY)

    def __and__(A, B):
        C_box = GameObject.box_intersection(A, B)

        if C_box is None:
            return False
        else:
            cx, cy, cX, cY = C_box
            return np.any(A.map[cx:cX, cy:cY] & B.map[cx:cX, cy:cY])
    
    @property
    def box(obj):
        """ (x_min, y_min, x_max, y_max)
        """
        x, y = obj.xy
        w, h = obj.w, obj.h
        return int(x-w/2), int(y-h/2), int(x+w/2), int(y+h/2)

class GIF(list):
    
    def __init__(gif, game, fname, start, stop, sound=None):
        assert "%d" in fname or "%i" in fname

        buffer = [ImageTk.PhotoImage((Image.open(fname % i))) for i in range(start, stop + 1)]
        list.__init__(gif, buffer)

        gif.canvas = game.canvas
        gif.lapse = game.GAME_LAPSE / 1_000

        gif.key = None

        gif.sound = sound

    def play(gif, x, y):
        thread.start_new(gif.__play, (x, y))

    def __play(gif, x, y):
        if gif.sound is not None:
            gif.sound.play()

        for frame in gif:
            gif.key = gif.canvas.create_image(x, y, image=frame)
            sleep(gif.lapse)
            gif.canvas.delete(gif.key)