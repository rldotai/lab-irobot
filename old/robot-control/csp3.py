"""
iRobot Create Serial Port Packet Processor (CSP3)
Converts a stream of raw bytes into sensor data from the robot.

Create Version 1 has packets of the form:
    19 <N> <id> <sensor> [<id> <sensor>, ...] <checksum>

Where `N` is the number of sensor bytes in the packet.
More information can be found at iRobot's website, but contrary to the 
documentation, the `start byte` (19) is included in the checksum calculation.

TODO: Better to use a list as a buffer, or implement a ring buffer? 
"""

import select
import struct 
import sys
import time
from time import sleep

import numpy as np 
import serial

import create_v1 as create 
from create_v1 import SERIAL_PARAMS, packet_dct 


class csp3:
    WAITING = 0
    IN_MSG = 1
    FIRST_BYTE = 19

    def __init__(self, sensor_lst):
        self.sensor_lst = sensor_lst
        self.packet_info = [packet_dct[i] for i in sensor_lst]
        self.names = [x['name'] for x in self.packet_info]
        self.sizes = np.array([x['size'] for x in self.packet_info])
        self.types = [i['dtype'] for i in self.packet_info]
        self.data_format = ">" + "".join(self.types)
        self.sensor_bytes = sum(self.sizes)
        self.total_bytes = len(self.sensor_lst) + self.sensor_bytes + 3

        # Determine locations in the packet that represent data
        id_ix = np.cumsum(np.append([2], self.sizes+1))[:-1]
        # get indices of sensor data within the packet
        self.data_ix = [id_ix[i] + j + 1 for i, x in enumerate(self.sizes) for j in range(x)]


        # Initialize the actual packet construction machinery
        self.buffer = []
        self.current = []
        self.count = 0
        self.checksum = 0
        self.state = csp3.WAITING


    def parse(self, pkt):
        """
        Parse the packet, first getting the data bytes (as integers), packing
        them, then unpacking them in the correct format.
        """
        ret = np.array(pkt)[self.data_ix]
        ret = struct.pack("B"*self.sensor_bytes, *ret)
        ret = struct.unpack(self.data_format, ret)
        return ret 

    def store(self, pkt):
        """Store the data from the packet."""
        dct = {k: v for k, v in zip(self.names, pkt)}
        print(dct) # TODO: REMOVE
        self.buffer.append(dct)

    def pop(self):
        """Pop a single element from the buffer."""
        if self.buffer:
            return self.buffer.pop(0)

    def flush(self):
        """Flush all data that has accumulated in the buffer."""
        ret = [i for i in self.buffer]
        self.buffer = []
        return ret

    def input(self, *byte_lst):
        """Input a series of bytes to the packet processor."""
        for b in byte_lst:
            self.input_byte(b)
    
    def input_byte(self, b):
        """Input a single byte to the packet processor."""
        if not isinstance(b, int):
            x = ord(b) # byte to integer
        
        # determine what to do with the byte, depending on state
        if self.state == csp3.WAITING:
            if x == csp3.FIRST_BYTE:
                self.count += 1
                self.checksum += x
                self.state = csp3.IN_MSG
                self.current = [x]
        elif self.state == csp3.IN_MSG:
            self.count += 1
            self.checksum += x
            self.current.append(x)
        else:
            raise RuntimeError("CSP3 in unrecognized state:", self.state)

        # if enough bytes have been accumulated, try to form a valid packet
        if self.count == self.total_bytes:
            if 0 == self.checksum % 256:
                packet = self.parse(self.current)
                self.store(packet)
            else:
                print("Misaligned packet:", self.current)

            # in either case, reset and be ready to form a new packet
            self.current = []
            self.count = 0
            self.checksum = 0
            self.state = csp3.WAITING







