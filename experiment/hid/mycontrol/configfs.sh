#!/bin/bash

# Exit on first error.
set -e

# Treat undefined environment variables as errors.
set -u

sleep 1

modprobe libcomposite

# Create gadget
mkdir /sys/kernel/config/usb_gadget/tablecontrol
cd /sys/kernel/config/usb_gadget/tablecontrol

# Add basic information
echo 0x0100 > bcdDevice # Version 1.0.0
echo 0x0200 > bcdUSB # USB 2.0
echo 0x00 > bDeviceClass
echo 0x00 > bDeviceProtocol
echo 0x00 > bDeviceSubClass
echo 0x10 > bMaxPacketSize0
echo 0x0104 > idProduct # Multifunction Composite Gadget
echo 0x1d6b > idVendor # Linux Foundation

# Create English locale
mkdir strings/0x409

echo "Bryan C. Jones" > strings/0x409/manufacturer
echo "Game Table Control" > strings/0x409/product
echo "8675309" > strings/0x409/serialnumber

# Create HID function
mkdir functions/hid.usb0

echo 1 > functions/hid.usb0/protocol
echo 9 > functions/hid.usb0/report_length # 9-byte reports
echo 0 > functions/hid.usb0/subclass # not a boot interface

# Write report descriptor
# KB Only
# echo "05010906a1018501050719e029e71500250175019508810275089501810175019503050819012903910275019505910175089506150026ff00050719002aff008100c0" | xxd -r -p > functions/hid.usb0/report_desc

# Mouse Only
# echo "05010902a10185020901a10005091901290314250175019503810275059501810105010930093109381581257f750895038106c0c0" | xxd -r -ps > functions/hid.usb0/report_desc

# Pen Only
# echo "050d0902a10185030920a10009420944093c0945150025017501950481029501810309328102950281030501093075109501a4550d65133500463a2026f85281020931462c18266c3e8102b4050d093026ff0081027508093d1581257f8102093e1581257f8102c0c0" | xxd -r -ps > functions/hid.usb0/report_desc

# Keyboard (ID=2) + Mouse (ID=2)
# echo "05010906a1018501050719e029e71500250175019508810275089501810175019503050819012903910275019505910175089506150026ff00050719002aff008100c005010902a10185020901a10005091901290314250175019503810275059501810105010930093109381581257f750895038106c0c0" | xxd -r -p > functions/hid.usb0/report_desc

# Keyboard (ID=1) + Mouse (ID=2) + Pen (ID=3)
echo "05010906a1018501050719e029e71500250175019508810275089501810175019503050819012903910275019505910175089506150026ff00050719002aff008100c005010902a10185020901a10005091901290314250175019503810275059501810105010930093109381581257f750895038106c0c0050d0902a10185030920a10009420944093c0945150025017501950481029501810309328102950281030501093075109501a4550d65133500463a2026f85281020931462c18266c3e8102b4050d093026ff0081027508093d1581257f8102093e1581257f8102c0c0" | xxd -r -p > functions/hid.usb0/report_desc

# Create configuration
mkdir configs/c.1
mkdir configs/c.1/strings/0x409

echo 0x80 > configs/c.1/bmAttributes
echo 2000 > configs/c.1/MaxPower # 2000 mA
echo "Example configuration" > configs/c.1/strings/0x409/configuration

# Link HID function to configuration
ln -s functions/hid.usb0 configs/c.1

sleep 2

# Enable gadget
ls /sys/class/udc > UDC

# sleep 15

echo "Done setting up gadget"

# /usr/local/bin/tester.sh &
# ./tester.sh &
# /usr/local/bin/tester.py &
