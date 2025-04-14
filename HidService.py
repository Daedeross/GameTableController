from enum import IntFlag

from Enums import ModifierKey
from HidState import HidState

def clamp(n, smallest, largest): return max(smallest, min(n, largest))

class HidService:
    # file path for reports
    _path = '/dev/hidg0'

    # keyboard
    _kb_report_id = 0

    # mouse
    _mouse_report_id = 2
    _b_button0 = 1
    _b_button1 = 1 << 1
    _b_button2 = 1 << 2

    # pen
    _pen_report_id = 3
    _b_in_range = 1 << 5
    _b_tip = 1
    _b_barrel = 1 << 1
    _b_eraser = 1 << 3
    _b_invert = 1 << 2

    max_x = 21240
    max_y = 15980

    def __init__(self, path = '/dev/hidg0'):
        self._path = path

    def _send(self, report: bytearray):
        try:
            with open(self._path, 'rb+') as fd:
                fd.write(report)
        except BlockingIOError:
            return

    def pen_report(self, x: int, y: int, in_range: bool, tip=False, barrel=False, eraser=False, invert=False):
        states = 0
        if(in_range):
            states = states | self._b_in_range
        if(barrel):
            states = states | self._b_barrel
        if(tip):
            states = states | self._b_tip
        if(eraser):
            states = states | self._b_eraser
        if(invert):
            states = states | self._b_invert
        x = clamp(x, 0, self.max_x)
        y = clamp(y, 0, self.max_y)
        output = bytearray(10)
        output[0] = self._pen_report_id
        output[1:2] = states.to_bytes(1, byteorder='little')
        output[2:4] = x.to_bytes(2, byteorder='little')
        output[4:6] = y.to_bytes(2, byteorder='little')
        self._send(output)

    def mouse_report(self, dx: int, dy: int, button0: bool, button1: bool, button2: bool, wheel: int = 0):
        if (dx < -127 or dx > 127):
            raise ("Invalid mouse x delta", dx)
        if (dy < -127 or dy > 127):
            raise ("Invalid mouse y delta", dy)
        if (wheel < -127 or wheel > 127):
            raise ("Invalid mouse wheel delta")

        states = 0
        if(button0):
            states |= self._b_button0
        if(button1):
            states |= self._b_button1
        if(button2):
            states |= self._b_button2
        output = bytearray(5)
        output[0] = self._mouse_report_id
        output[1:2] = states.to_bytes(1, byteorder='little')
        output[2:3] = dx.to_bytes(1, byteorder='little', signed = True)
        output[3:4] = dy.to_bytes(1, byteorder='little', signed = True)
        output[4:5] = wheel.to_bytes(1, byteorder='little', signed = True)
        self._send(output)

    def kb_report(self, modifiers: ModifierKey, keys_set: set[int] = []):
        keys = [k for k in keys_set]
        if len(keys) > 6:
            keys = keys[0:6]
        else:
            while len(keys) < 6:
                keys.append(0)

        output = bytearray(9)
        output[0] = self._kb_report_id
        # byte 0 : modifier
        output[1:2] = modifiers.to_bytes(1, byteorder='little')
        # byte 1 : reseverd
        # bytes 2-7 : key codes
        for i in range(0, 6):
            output[i+3:i+4] = keys[i].to_bytes(1, byteorder='little')
        # for key in keys:
        #     output.append(key.to_bytes(1, byteorder='little'))

    def full_report(self, state: HidState):
        self.pen_report(state.x, state.y, state.in_range)
        self.mouse_report(0, 0, state.mouse0, state.mouse1, state.mouse2, state.wheel_delta)
        self.kb_report(ModifierKey.NONE, state.keys)
        state.wheel_delta = 0 # reset delta