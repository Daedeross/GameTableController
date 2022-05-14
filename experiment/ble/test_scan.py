
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# from picamera.array import PiRGBArray
# from picamera import PiCamera

import time
import cv2

MAX_RETRIES = 4

radio = BLERadio()
print("scanning")
found = set()
peer = None
for entry in radio.start_scan(timeout=60, minimum_rssi=-80):
    addr = entry.address
    if addr not in found:
        print(entry)
        if entry.complete_name == "Game Table Controller":
            peer = entry
            found.add(addr)
            break
    found.add(addr)
radio.stop_scan()
print("scan done")

if peer != None:
    print("connecting")
    retries = 0
    while retries < MAX_RETRIES:
        try:
            connection = radio.connect(peer)
            break
        except:
            retries = retries + 1
            time.sleep(1)
    print("connected")
    uart = connection[UARTService]
    #buf = bytearray(255)
    while True:
        while uart.in_waiting > 0:
            buf = uart.read(1)
            print("{:08b}".format(buf[0]))
            #uart.reset_input_buffer()
        time.sleep(0.001)
