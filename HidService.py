
from curses import mouseinterval


class HidService:
    #
    _path = '/dev/hidg0'

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

    def pen_report(self, x: int, y: int, in_range: bool, tip=False, barrel=False, eraser=False, invert=False):
        with open(self._path, 'rb+') as fd:
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
            output = bytearray(10)
            output[0] = self._pen_report_id
            output[1:2] = states.to_bytes(1, byteorder='little')
            output[2:4] = x.to_bytes(2, byteorder='little')
            output[4:6] = y.to_bytes(2, byteorder='little')
            fd.write(output)

    def mouse_report(self, dx: int, dy: int, button0: bool, button1: bool, button2: bool, wheel: int = 0):
        if (dx < -127 or dx > 127):
            raise ("Invalid mouse x delta", dx)
        if (dy < -127 or dy > 127):
            raise ("Invalid mouse y delta", dy)
        if (wheel < -127 or wheel > 127):
            raise ("Invalid mouse wheel delta")
        
        with open(self._path, 'rb+') as fd:
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
            fd.write(output)

    def full_report(self, x: int, y: int, in_range: bool, button0: bool, button1: bool, button2: bool, wheel: int = 0):
        self.pen_report(x, y, in_range)
        self.mouse_report(0, 0, button0, button1, button2)