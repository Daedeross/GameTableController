#!/usr/bin/env python3
import time

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from picamera2.picamera2 import Picamera2
import cv2
import numpy as np

from time import sleep

path = '/dev/hidg0'

report_id = 3

b_in_range = 1 << 5
b_tip = 1
b_barrel = 1 << 1
b_eraser = 1 << 3
b_invert = 1 << 2

def pen_report(x, y, in_range, tip=False, barrel=False, eraser=False, invert=False):
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
        if(invert):
            states = states | b_invert
        output = bytearray(10)
        output[0] = report_id
        output[1:2] = states.to_bytes(1, byteorder='little')
        output[2:4] = x.to_bytes(2, byteorder='little')
        output[4:6] = y.to_bytes(2, byteorder='little')
        fd.write(output)

b0_down = 0b10000000
b0_up   = 0b01000000
b1_down = 0b00100000
b1_up   = 0b00010000
b2_down = 0b00001000
b2_up   = 0b00000100
button0 = False
button1 = False
button2 = False

MAX_RETRIES = 10

params = cv2.SimpleBlobDetector_Params()

# Change thresholds
params.minThreshold = 10
params.maxThreshold = 200

# Filter by Color (Black<->White)
params.filterByColor = True
params.blobColor = 255

detector = cv2.SimpleBlobDetector_create(params)
max_x = 21240
max_y = 15980
size = (1024, 768)
cv2.startWindowThread()
picam2 = Picamera2()
picam2.start_preview()
picam2.configure(picam2.preview_configuration(main={"format": 'XRGB8888', "size": size}))
picam2.start()

ble = BLERadio()

def keypoints():
    im = picam2.capture_array()

    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    keypoints = detector.detect(gray)
    # print(len(keypoints))
    im_with_keypoints = cv2.drawKeypoints(gray, keypoints, np.array([]), (0,255,0), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    cv2.imshow("Camera", im_with_keypoints)
    if any(keypoints):
        kp = keypoints[0]
        x = max_x - round(kp.pt[0] * max_x / size[0])
        y = round(kp.pt[1] * max_y / size[1])
        #print(x, y)

        pen_report(x, y, True, button1, button2, button0)

def buttons(b):
    global button0
    global button1
    global button2
    if b & b0_down:
        button0 = True
    elif b & b0_up:
        button0 = False
    if b & b1_down:
        button1 = True
    elif b & b1_up:
        button1 = False
    if b & b2_down:
        button2 = True
    elif b & b2_up:
        button2 = False
    #print(button2)

while True:
    while ble.connected and any(
        UARTService in connection for connection in ble.connections
    ):
        connected = False
        for connection in ble.connections:
            if UARTService not in connection:
                continue
            connected = True
            uart = connection[UARTService]
            while uart.in_waiting > 0:
                buf = uart.read(1)
                buttons(buf[0])
                #print("{:08b}".format(buf[0]))
        if connected:
            keypoints()

    print("disconnected, scanning")
    for advertisement in ble.start_scan(ProvideServicesAdvertisement, timeout=1):
        print(advertisement.complete_name)
        if UARTService not in advertisement.services:
            continue
        print("conecting to")
        print(advertisement.complete_name)
        retries = 0
        while retries < MAX_RETRIES:
            try:
                connection = ble.connect(advertisement)
                break
            except:
                retries = retries + 1
                time.sleep(1)
        print("connected")
        break
    ble.stop_scan()