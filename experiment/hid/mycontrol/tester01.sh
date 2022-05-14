#!/bin/bash
#
# Bash file to test the gadget by writing "Hello World!"
# If used with the configfs_test.sh, place this file under /usr/local/bin/tester.sh
# and uncomment the appropriate line

function write_report {
    echo -ne $1 > /dev/hidg0
}

sleep 5


# pen to (100, 100)
write_report "\x3\0\x64\0\x64\0\0\0\0\0"

# pen to (200, 200)
write_report "\x3\0\xc8\0\xc8\0\0\0\0\0"
