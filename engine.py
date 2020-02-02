import datetime as dt
import _thread as thread

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font, nametofont

import numpy as np

from math import pi, sin, cos, e, sqrt, floor, ceil

from time import perf_counter as clock
from time import sleep

from PIL import Image, ImageTk

import random
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
        dxdy : func (game, x, y) -> dx, dy
        boom : func (game, x, y) -> None
    """

    img = None

    map = None

    game = None

    group = None

    was_init = False

    def __init__(obj, x, y, dxdy = None, boom = None):
        obj.key = obj.game.canvas.create_image(x, y, image=obj.tkimg)

        obj.dxdy = dxdy if dxdy is not None else obj.__dxdy
        obj.boom = boom if boom is not None else obj.__boom

    def __hash__(obj):
        return obj.key

    def __dxdy(obj, game, x, y):
        return 0, 0

    def __boom(obj, game, x, y):
        return

    def move(obj):
        dxdy = obj.dxdy(obj.game, *obj.xy)

        ## Object got out of the screen or something...
        if dxdy is None:
            obj.erase()
        else:
            obj.game.canvas.move(obj.key, *dxdy)

    def erase(obj):
        obj.game.canvas.delete(obj.key)
        obj.cls.group.remove(obj)
        obj.boom(game)
        
    @property
    def xy(obj):
        return obj.game.canvas.coords(obj.key)

    @property
    def x(obj):
        return obj.xy[0]
    
    @property
    def y(obj):
        return obj.xy[1]

    @classmethod
    def init(cls, game):
        cls.game = game
        cls.init_img()
        cls.init_group()

        cls.was_init = True

        return cls.group

    @classmethod
    def init_group(cls):
        cls.group = Group()

    @classmethod
    def init_img(cls):
        cls.shape = img.size

        cls.w, cls.h = obj.shape

        cls.w_2 = cls.w // 2
        cls.h_2 = cls.h // 2

        ## Tkinter Image
        cls.tkimg = ImageTk.PhotoImage(cls.img)
        
        ## Image Map
        array = np.array(img.convert("RGBA"))
        cls.map = np.array(array[:,:,3], dtype=np.bool)

    @property
    def cls(obj):
        return obj.__class__

class GameObject(BaseObject):
    """ Used to define a game object, such as spacecraft or meteors.
        canvas : tk.Canvas object
        img : PIL.Image object
        x, y : int
        dxdy : func
        boom : func
    """

    def __init__(obj, x, y, dxdy = None, boom = None):
        BaseObject.__init__(obj, x, y, dxdy, boom)

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

    def shadow(A, C_box):
        ax, ay, aX, aY = A.box
        cx, cy, cX, cY = C_box
        return A.map[cx-ax:cX-aX, cy-ay:cY-aY]

    def __and__(A, B):
        C_box = GameObject.box_intersection(A, B)

        if C_box is None:
            return False
        else:
            cx, cy, cX, cY = C_box
            AS, BS = A.shadow(C_box), B.shadow(C_box)
            assert AS.shape == BS.shape
            return np.any(AS & BS)
    
    @property
    def box(obj):
        """ (x_min, y_min, x_max, y_max)
        """
        x, y = obj.xy
        w, h = obj.w, obj.h

        return int(x-w/2), int(y-h/2), int(x+w/2), int(y+h/2)

class Group(set):

    __binds__ = []

    def __init__(self, buffer=None):
        set.__init__(self, buffer if buffer is not None else [])

    @classmethod
    def bind(cls, A, B, action):
        """ Add Action for collision.
        """
        cls.__binds__.append((A, B, action))

    @classmethod
    def collide(cls):
        """ This could be smarter. But it isn't
        """
        for A, B, action in cls.__binds__:
            for a in A:
                for b in B:
                    if (a & b): action(a, b)

class GIF(list):
    
    def __init__(gif, game, fname, start, stop, sound_fname=None):
        assert "%d" in fname or "%i" in fname

        buffer = [ImageTk.PhotoImage((Image.open(fname % i))) for i in range(start, stop + 1)]
        list.__init__(gif, buffer)

        gif.canvas = game.canvas
        gif.lapse = game.GAME_LAPSE / 1_000

        gif.key = None

        gif.sound = Sound(sound_fname) if sound_fname is not None else None

    def play(gif, x, y):
        thread.start_new(gif.__play, (x, y))

    def __play(gif, x, y):
        if gif.sound is not None:
            gif.sound.play()

        for frame in gif:
            gif.key = gif.canvas.create_image(x, y, image=frame)
            sleep(gif.lapse)
            gif.canvas.delete(gif.key)