import time

from enum import Enum
from BluetoothService import BluetoothService, BleEvent
from HidService import HidService
from VisionServcie import VisionService

from picamera2.picamera2 import *
import cv2
import numpy as np

class Mode(Enum):
    MOUSE = 1
    PEN = 2
    KEYBOARD = 3

class Controller:
    flip_x = True
    flip_y = False

    def __init__(self, mode: Mode, bluetooth: BluetoothService, vision: VisionService, hid: HidService):
        self.mode = mode
        self._bluetooth = bluetooth
        self._vision = vision
        self._hid = hid
        self.button0 = False
        self.button1 = False
        self.button2 = False
        self._last_x = 0
        self._last_y = 0
        self._bluetooth.set_callback(1, self._handle_packet)
        
    def toggle_buttons(self, packet):
        if packet & BleEvent.B0_DOWN:
            self.button0 = True
        elif packet & BleEvent.B0_UP:
            self.button0 = False
        if packet & BleEvent.B1_DOWN:
            self.button1 = True
        elif packet & BleEvent.B1_UP:
            self.button1 = False
        if packet & BleEvent.B2_DOWN:
            self.button2 = True
        elif packet & BleEvent.B2_UP:
            self.button2 = False

    def _handle_packet(self, bytes: bytearray):
        self.toggle_buttons(bytes[0])

    def _mouse_mode(self, point):
        x = round(point[0])
        y = round(point[1])
        deltax = x - self._last_x
        deltay = x - self._last_y
        self._last_x = x
        self._last_y = y
        # break up deltas into multiple reports if needed
        while not (deltax == 0 and deltay == 0):
            dx = 127 if deltax > 127 else -127 if deltax < -127 else deltax
            dy = 127 if deltay > 127 else -127 if deltay < -127 else deltay
            self._hid.mouse_report(dx, dy, self.button0, self.button1, self.button2, 0)
            deltax -= dx
            deltay -= dy

    def _pen_mode(self, point: tuple):
        if point:
            in_range = True
            x = round(point[0] * self._hid.max_x / self._vision.size[0])
            y = round(point[1] * self._hid.max_y / self._vision.size[1])
            if self.flip_x:
                x = self._hid.max_x - x
            if self.flip_y:
                y = self._hid.max_y - y
            self._last_x = x
            self._last_y = y
        else:
            in_range = False
        self._hid.full_report(self._last_x, self._last_y, in_range, self.button1, self.button2, self.button0)

    def _do_output(self, point):
        if self.mode == Mode.MOUSE:
            self._mouse_mode(point or (self._last_x, self._last_y))
        elif self.mode == Mode.PEN:
            self._pen_mode(point)

    def _loop(self):
        self._bluetooth.ensure_ready()
        self._bluetooth.read_uart()
        keypoints = self._vision.get_keypoints()
        if any(keypoints):
            self._do_output(keypoints[0])
        else:
            self._do_output(None)

    def run(self):
        self._vision.uart_callibrate(self._bluetooth)
        while True:
            self._loop()

if __name__ == '__main__':
    controller = Controller(Mode.PEN, BluetoothService(), VisionService(size = (800, 600)), HidService())
    # controller._vision._show_points = True
    controller.run()