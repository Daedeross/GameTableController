from ctypes import ArgumentError
from enum import Enum
import time
from tkinter import N

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

class BleEvent:
    B0_DOWN = 0b10000000
    B0_UP   = 0b01000000
    B1_DOWN = 0b00100000
    B1_UP   = 0b00010000
    B2_DOWN = 0b00001000
    B2_UP   = 0b00000100

    ANY_DOWN = B0_DOWN | B1_DOWN | B2_DOWN
    ANY_UP   = B0_UP   | B1_UP   | B2_UP

def NoOp():
    pass

class BluetoothService:
    _MAX_RETRIES = 10

    def __init__(self, radio: BLERadio = None):        
        self._radio = radio or BLERadio()
        self._packet_size = 1
        self._packet_callback = NoOp

    def _get_uart_connection(self, name = None):
        self._connection = None
        self._uart = None
        print("disconnected, scanning")
        while self._connection == None:
            for advertisement in self._radio.start_scan(ProvideServicesAdvertisement, timeout=1):
                print(advertisement.complete_name)
                if UARTService not in advertisement.services:# or (name and advertisement.complete_name != name):
                    continue
                print("conecting to")
                print(advertisement.complete_name)
                retries = 0
                while retries < self._MAX_RETRIES:
                    try:
                        self._connection = self._radio.connect(advertisement)
                        self._uart = self._connection[UARTService]
                        break
                    except:
                        retries = retries + 1
                        time.sleep(1)
                print("connected")
                break
        self._radio.stop_scan()

    def set_callback(self, packet_size: int, callback):
        if packet_size != None and packet_size < 1:
            raise ArgumentError(packet_size)

        self._packet_size = packet_size or 1
        self._packet_callback = callback

    def get_callack(self):
        if self._packet_callback and self._packet_size:
            return self._packet_size, self._packet_callback

    def connected(self):
        return self._radio.connected

    def ready(self):
        return self._radio.connected and self._connection and self._uart

    def ensure_ready(self):
        if not self.ready():
            self._get_uart_connection()

    def read_uart(self):
        while self._uart.in_waiting >= self._packet_size:
            buf = self._uart.read(self._packet_size)
            if self._packet_callback:
                self._packet_callback(buf)