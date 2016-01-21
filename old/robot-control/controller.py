"""
Code for controlling the iRobot Create.

TODO: Ensure sleep called as infrequently and for as short a time as possible
"""
import select
import struct

import serial
from time import sleep, time 

import create_v1 as create 
from csp3 import csp3

class Controller:
    def __init__(port_name, serial_params):
        self.ser = open_port(port_name, serial_params)

    def open_port(self, port_name, serial_params):
        """Open a serial port for connecting to the robot."""
        try:
            ser = serial.Serial(port_name, **serial_params)
            ser.setRTS(0)
            sleep(0.25)
            ser.setRTS(1)
            sleep(0.25)
            ser.flushOutput()
            sleep(0.25)
        except Exception as e:
            raise(e)
        return ser 


    def shutdown(self):
        """Shutdown. Pause stream, set mode to passive, and close serial port."""
        try:
            self.pause_stream(self)
            sleep(1.5)
            self.ser.flushOutput()
            self.mode_passive(self)
            sleep(1.5)
        except Exception as e:
            self.ser.flush()
            self.ser.flushOutput()
            self.ser.flushInput()
            self.ser.close()
            raise(e)

    def send_cmd(self, lst):
        """Send a command (here, a list of integers) to the robot."""
        cmd = struct.pack('B'*len(lst), *lst)
        try:
            sent = self.ser.write(cmd)
            self.ser.flush()
            return sent
        except Exception as e:
            raise(e)

    def mode_full(self):
        """Set mode to full."""
        pass

    def mode_passive(self):
        """Set mode to passive."""
        return self.send_cmd([create.OP_PASSIVE])

    def pause_stream(self):
        """Pause the stream."""
        return self.send_cmd([create.OP_PAUSE, 0])

    def request_stream(self, sensor_ids):
        """Request a stream of the sensors specified by `sensor_ids`."""
        length = len(sensor_ids)
        cmd_lst = [create.OP_STREAM, length] + sensor_ids
        return self.send_cmd(cmd_lst)

    def soft_reset(self):
        """Soft reset (an undocumented function)."""
        pass


def main(port, sensor_ids):
    # Open the serial port
    try:
        print("Opening port at:", port)
        ser = open_port(port, create.SERIAL_PARAMS)
        fd = ser.fileno()
        ser.nonblocking() # set serial port to non-blocking

    except Exception as e:
        raise(e)

    try:
        # Set mode to passive
        mode_passive(ser)

        # Request sensor data and set up handler
        pp = csp3(sensor_ids)
        request_stream(ser, sensor_ids)

        start = time()
        while time() - start < 1:
            ready, *_ = select.select([fd], [], [], 5)
            data = ser.read()
            # print(ready, ord(data))
            pp.input(data)

    finally:
        print("Shutting down...")
        shutdown(ser)

if __name__ == "__main__":
    port_name = '/dev/ttyUSB0'
    pkt_ids = [7, 25, 8]
    main(port_name, pkt_ids)
