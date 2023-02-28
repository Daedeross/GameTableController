# Game Table Controller

This repository contains code for running my gaming table.

There are two parts of this project, so far: a Handheld controller and a Raspberry Pi

### Handheld Controller

The handheld controller is an Arduino board, currently an [Adafruit Feather nRF52840 Express](https://www.adafruit.com/product/4062), though the code _should_ work on any nRF52840 board. The controller is hooked up to three buttons, an IR LED, and a power switch. It communicates button presses to the Raspberry Pi via UART using Bluetooth Low Energy.

### Raspberry Pi

Currently, this is a Raspberry Pi 4 4GB. The rpi emulates a USB HID device by utilizing the [Linux-USB Gadget API](http://www.linux-usb.org/gadget/). The Raspberry Pi must be a V4, Zero W, or Zero 2 W because these models have the propper type of USB port to act as a USB peripheral. 

The Raspberry Pi Zero W is not powerfull enough to do the optical position required and RPi Zero 2 Ws are impossible to come by, so I am using an RPi 4 for now.

The RPi connects to the arduino via Bluetooth Low Energy and listens for UART packets and sends those as USB button clicks. Position is determined by using a camera and OpenCV to track an IR LED in the controller and sending these data as X,Y of a USB Pen/Tablet device. (Buttons are sent as mouse buttons because not all VTT programs play nice with pen buttons, but this is easiy changed)  

## Installing

### Arduino
- Upload the Arduino code to the Hand Controller
### Raspberry Pi
- Enable the USB-HID gadget
  - This can be done several ways. I don't remember exactly how I set it up to run automatically, but the script that runs is [this one](experiment/hid/mycontrol/configfs.sh)
- Install [Adafruit CircuitPython BLE](https://github.com/adafruit/Adafruit_CircuitPython_BLE)
- Install or compile OpenCV with python bindings.
  - [Instructions](https://qengineering.eu/install-opencv-4.5-on-raspberry-64-os.html) 
- Install [Picamera2](https://github.com/raspberrypi/picamera2)
  - Still in pre-release
  - Have to build it and `libcamera` yourself.
  - Follow their instructions.

## Runing the table

- Turn on the controller
- Run the Controller.py script
  - The script will first configure the camera. Click any button on the controller when it is at each of the for corners of the projected screen.
- Now it will send Pen and Mouse reports via USB to the attached computer that is running the VTT or game.

## Future Work

I am trying several things right now, which may or may not bear fruit:
- Audomatic callibration
  - There projection is not bright enough on the back-side for the Canny algorithm to find its edges consistently.
  - Also, I have to remove the IR lowpass-filter for the camera to even see the projection, kinda eliminating the point of automatic callibration. Maybe if I get a camera with a motorized switchable filter.
- Track AR markers on the base of miniatures.
  - Several issues with this so far:
    1. The glass tabletop is 1/4 inch thick and the diffusion film is on the bottom, so things ontop are quite blurred, making it hard for the markers to be detected
    2. Lighting, Strong IR light will need to be thrown at the back of the screen for the markers to show up.
       - Possible to create self-illuminated bases, but that sound like an entire project in its own right.
    3. Would probably have to use a custom VTT, or maybe some kind of API to send the positions to the program. Again, sounds like a big project by itself.
- C/C++ implementation
  - Performance is _OK_ on Python, but I'm sure C would be faster.
  - This will probably reduce processing time currently spent re-allocating memory for and garbage collecting all the numpy arrays.
  - I am still looking around for a good C/C++ Bluetooth LE library.

## Contributing

Hah, this is for personal use, but feel free to fork or whatever. PRs will probably not be accepted.
