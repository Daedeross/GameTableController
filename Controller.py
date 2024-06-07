from enum import Enum
from BluetoothService import BluetoothService
from Enums import BleEvent, BleBtnState
from HidService import HidService
from VisionServcie import VisionService
from HidState import HidState
from ControllerStateMachine import ControllerStateMachine

from _bleio.exceptions import BluetoothError
from picamera2.picamera2 import *
import cv2
import numpy as np

recalibrate_mask = BleBtnState.BTN_0 | BleBtnState.BTN_1 | BleBtnState.ENC_SELECT

class Mode(Enum):
    MOUSE = 1
    PEN = 2
    KEYBOARD = 3

class Controller:
    __version = 2
    flip_x = True
    flip_y = False

    def __init__(self, mode: Mode, bluetooth: BluetoothService, vision: VisionService, hid: HidService, version = 2):
        self.mode = mode
        self.recalibrate = False
        self._bluetooth = bluetooth
        self._vision = vision
        self._hid = hid
        self._hid_state = HidState()
        self.flip_x = False
        self.flip_y = True
        self._bluetooth.set_callback(1 if version == 1 else 2, self._handle_packet)
        self._state_machine = self.__wire_state_machine()
        self.__version = version
        self._hid_state.set_callback(recalibrate_mask, self._request_calibrate)

    def __wire_state_machine(self) -> ControllerStateMachine:
        sm = ControllerStateMachine()
        sm.set_enter_callback("scanning", self.on_scanning)
        sm.set_enter_callback("connecting", self.on_connecting)
        sm.set_enter_callback("calibrating", self.on_calibrating)
        sm.set_enter_callback("running", self.on_running)
        return sm

    def _request_calibrate(self, state):
        self.recalibrate = True

    def _toggle_buttons(self, packet):
        if packet & BleEvent.B0_DOWN:
            self._hid_state.mouse0 = True
        elif packet & BleEvent.B0_UP:
            self._hid_state.mouse0 = False
        if packet & BleEvent.B1_DOWN:
            self._hid_state.mouse1 = True
        elif packet & BleEvent.B1_UP:
            self._hid_state.mouse1 = False
        if packet & BleEvent.B2_DOWN:
            self._hid_state.mouse2 = True
        elif packet & BleEvent.B2_UP:
            self._hid_state.mouse2 = False

    def _handle_packet(self, bytes: bytearray):
        if self.__version == 1:
            self._toggle_buttons(bytes[0])
        elif self.__version == 2:
            self._hid_state.wheel_delta = int.from_bytes(bytes[0:1], byteorder='little', signed=True)
            self._hid_state.apply_buttons(bytes[1])

    def _mouse_mode(self, point):
        x = round(point[0])
        y = round(point[1])
        deltax = x - self._hid_state.last_x
        deltay = x - self._hid_state.last_y
        deltaw = self._hid_state.wheel_delta
        self._hid_state.last_x = x
        self._hid_state.last_y = y
        # break up deltas into multiple reports if needed
        while not (deltax == 0 and deltay == 0 and deltaw == 0):
            dx = 127 if deltax > 127 else -127 if deltax < -127 else deltax
            dy = 127 if deltay > 127 else -127 if deltay < -127 else deltay
            self._hid.mouse_report(dx, dy, self._hid_state.mouse0, self._hid_state.mouse1, self._hid_state.mouse2, deltaw)
            deltax -= dx
            deltay -= dy
            deltaw = 0  # wheel delta is already clamped, so only apply once

    def _pen_mode(self, point: tuple):
        if point:
            self._hid_state.in_range = True
            x = round(point[0] * self._hid.max_x / self._vision.size[0])
            y = round(point[1] * self._hid.max_y / self._vision.size[1])
            if self.flip_x:
                x = self._hid.max_x - x
            if self.flip_y:
                y = self._hid.max_y - y
            self._hid_state.last_x = x
            self._hid_state.x = x
            self._hid_state.last_y = y
            self._hid_state.y = y
        else:
            self._hid_state.in_range = False
        self._hid.full_report(self._hid_state)

    def _do_output(self, point):
        if self.mode == Mode.MOUSE:
            self._mouse_mode(point or (self._hid_state.last_x, self._hid_state.last_y))
        elif self.mode == Mode.PEN:
            self._pen_mode(point)
        else:
            print(f"ERROR - Unsupported MODE: {self.mode}")

    def _loop(self):
        if not self._bluetooth.connected():
            return "scan"

        self._bluetooth.read_uart()
        if self.recalibrate:
            return "calibrate"

        keypoints = self._vision.get_keypoints()
        if any(keypoints):
            self._do_output(keypoints[0])
        else:
            self._do_output(None)

    def run(self):
        self._state_machine.scan()
        # self._vision.uart_callibrate(self._bluetooth)
        # while True:
        #     self._loop()

    def on_scanning(self):
        print("Scanning")
        self._bluetooth.ensure_ready()
        self._state_machine.connect()

    # this state is only here if I decide to attach a logger or something
    # scanning and connecting are all handled in the same loop within
    # the BLE service
    def on_connecting(self):
        self._state_machine.calibrate()

    def on_calibrating(self):
        try:
            self.recalibrate = False
            self._bluetooth.send_text("Calibrating...")
            self._vision.uart_callibrate(self._bluetooth)
            self._state_machine.loop()
        except BluetoothError:
            print("BluetoothError: now rescanning")
            self._state_machine.scan()
            return

    def on_running(self):
        next = None
        try:
            self._bluetooth.send_text("Running...")
            while not next:
                next = self._loop()

            self._state_machine.send(next)
        except BluetoothError:
            print("BluetoothError: now rescanning")
            self._state_machine.scan()

if __name__ == '__main__':
    controller = Controller(Mode.PEN, BluetoothService(), VisionService(version = 2, size = (800, 600)), HidService(), version = 2)
    # controller._vision._show_points = True
    controller.run()