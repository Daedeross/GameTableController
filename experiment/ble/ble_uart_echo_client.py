# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Used with ble_uart_echo_test.py. Transmits "echo" to the UARTService and receives it back.
"""

import time

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

ble = BLERadio()
while True:
    while ble.connected and any(
        UARTService in connection for connection in ble.connections
    ):
        for connection in ble.connections:
            if UARTService not in connection:
                continue
            uart = connection[UARTService]
            # uart.write(b"echo")
            # Returns b'' if nothing was read.
            one_byte = uart.read(4)
            if one_byte:
                print(one_byte)
        #time.sleep(1)

    print("disconnected, scanning")
    for advertisement in ble.start_scan(ProvideServicesAdvertisement, timeout=1):
        if UARTService not in advertisement.services:
            continue
        print("conecting to")
        print(advertisement.complete_name)
        ble.connect(advertisement)
        print("connected")
        break
    ble.stop_scan()