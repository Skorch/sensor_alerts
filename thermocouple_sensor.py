#!/usr/bin/env python
#  -*- coding: utf-8 -*-
"""
    MCC 134 Functions Demonstrated:
        mcc134.t_in_read
    Purpose:
        Read a single data value for each channel in a loop.
    Description:
        This example demonstrates acquiring data using a software timed loop
        to read a single value from each selected channel on each iteration
        of the loop.
"""
from __future__ import print_function
from time import sleep
from sys import stdout
from daqhats import mcc134, HatIDs, HatError, TcTypes
from daqhats_utils import select_hat_device, tc_type_to_string
import logging

DEBUG = True

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

# Constants
CURSOR_BACK_2 = '\x1b[2D'
ERASE_TO_END_OF_LINE = '\x1b[0K'
tc_type = TcTypes.TYPE_J   # change this to the desired thermocouple type

def get_temps():
    channels = (0, 1, 2, 3)

    # Get an instance of the selected hat device object.
    address = select_hat_device(HatIDs.MCC_134)
    hat = mcc134(address)

    for channel in channels:
        hat.tc_type_write(channel, tc_type)

    try:
        samples_per_channel = 0

        # Read a single value from each selected channel.
        for channel in channels:
            samples_per_channel += 1
            value = hat.t_in_read(channel)

            if value == mcc134.OPEN_TC_VALUE:
                logger.debug(f"Channel {channel} open ({mcc134.OPEN_TC_VALUE}).")
            elif value == mcc134.OVERRANGE_TC_VALUE:
                logger.warn(f"Channel {channel} over range.")
                
            elif value == mcc134.COMMON_MODE_TC_VALUE:
                logger.warn(f"Channel {channel} common mode TC.")
            else:
                yield (channel, value)


    except (HatError, ValueError) as error:
        logger.error(error)





if __name__ == '__main__':

    for channel, value in get_temps():
        if value:
            print(f"Channel - {channel}: {value}")
