#!/usr/bin/env python3
#
# Python file to test the gadget by moving the cursor

from operator import inv
from time import sleep

path = '/dev/hidg0'

report_id = 3

b_in_range = 1 << 5
b_barrel = 1 << 1
b_tip = 1
b_eraser = 1 << 3
b_invert = 1 << 2

def report(x, y, in_range, barrel=False, tip=False, eraser=False, invert=False):
    with open(path, 'rb+') as fd:
        states = 0
        if(in_range):
            states = states | b_in_range
        if(barrel):
            states = states | b_barrel
        if(tip):
            states = states | b_tip
        if(eraser):
            states = states | b_eraser
        if(inv):
            states = states | b_invert

        output = bytearray(10)
        output[0] = report_id
        output[1:2] = states.to_bytes(1, byteorder='little')
        output[2:4] = x.to_bytes(2, byteorder='little')
        output[4:6] = y.to_bytes(2, byteorder='little')

        fd.write(output)

sleep(5)

report(300, 0, True)

sleep(5)

report(1000, 100, True)
