"""
Code for controlling the iRobot Create.

TODO: Ensure sleep called as infrequently and for as short a time as possible
"""
import select
import serial
import struct
from time import sleep, time 

import create_v1 as create 
from csp3 import csp3


class Controller:
    def __init__(self, port_name, serial_params):
        self.ser = self.open_port(port_name, serial_params)

    @staticmethod
    def open_port(port_name, serial_params):
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
            self.pause_stream()
            sleep(1.5)
            self.ser.flushOutput()
            self.mode_passive()
            sleep(1.5)
        except Exception as e:
            self.ser.flush()
            self.ser.flushOutput()
            self.ser.flushInput()
            self.ser.close()
            raise(e)
        finally:
            self.ser.close()

    def send_cmd(self, *lst):
        """Send a command (here, a list of integers) to the robot.

        Args:
            lst: a list of int, or other byte-sized objects.

        Returns:
            int: the number of bytes sent 
        """
        print(lst)
        print(len(lst))
        cmd = struct.pack('B'*len(lst), *lst)
        try:
            sent = self.ser.write(cmd)
            self.ser.flushOutput()
        except Exception as e:
            raise(e)
        return sent

    def mode_full(self):
        """Set mode to full."""
        self.send_cmd(create.OP_FULL)

    def mode_passive(self):
        """Set mode to passive."""
        return self.send_cmd(create.OP_PASSIVE)

    def pause_stream(self):
        """Pause the stream."""
        return self.send_cmd(create.OP_PAUSE, 0)

    def request_stream(self, *sensor_ids):
        """Request a stream of the sensors specified by `sensor_ids`."""
        length = len(sensor_ids)
        print(sensor_ids)
        return self.send_cmd(create.OP_STREAM, length, *sensor_ids)

    def run_demo(self, num):
        """Run a built-in demo.
        num : 0, 1, 2, ..., 9
        """
        ret = self.stop_demo()
        ret += self.send_cmd(create.OP_DEMO, num)
        return ret 

    def stop_demo(self):
        return self.send_cmd(create.OP_DEMO, 255)

    def set_led(self, playOn=False, advOn=False, powColor=0, powIntensity=0):
        # Set up byte for the Advance and Play LEDs
        tmp = 0
        # do these with binary operators to make them more obvious
        if playOn: tmp += 1
        if advOn:  tmp += 8 
        # Limit the power LED intensities
        powIntensity = max(0, min(powIntensity, 255))
        powColor     = max(0, min(powColor, 255))
        
        # send the command
        return self.send_cmd(OP_LEDS, tmp, powColor, powIntensity)

    def set_lsd(self, d0=False, d1=False, d2=False):
        """ Set the low side drivers to be on (True) or off (False)
            d0 and d1 (corresponding to pins 22 & 23) have a maximum current
            of 0.5 A, d2 (pin 24) has a maximum current of 1.5 """
        # Build the byte to be sent to the Create
        tmp = 0
        if d0: tmp += 1
        if d1: tmp += 2
        if d2: tmp += 4
        
        # send the command
        return self.send_cmd(OP_LSD, tmp)

    def pwm_lsd(ser, pct0=0, pct1=0, pct2=0):
        """ Set up pulse-width modulation on the low side drivers by specifying
        the percentage of maximum power (w/ 7 bit resolution)."""
        # Get the integer representation of the desired power
        d0 = max(0, min(int(128 * pct0), 128))
        d1 = max(0, min(int(128 * pct1), 128))
        d2 = max(0, min(int(128 * pct2), 128))
        # Send the command 
        return self.send_cmd(OP_PWM_LSD, d0, d1, d2)

    def soft_reset(self):
        """Soft reset (an undocumented function).
        Useful when the Create has been switched to Passive Mode WHILE power is 
        available  -- it apparently only detects the rising current, so it might
        not actually begin charging.
        This is a somewhat undocumented feature (but is mentioned in the iRobot
        website support FAQ). It forces the robot to run its bootloader.

        IMPORTANT: DO NOT SEND ANY DATA WHILE BOOTLOADER IS RUNNING! 
        It takes about three (3) seconds to run the bootloader.
        """
        try:
            ret = self.send_cmd(create.OP_SOFT_RESET)
        except Exception as e:
            print(e)
        finally:
            sleep(3)
        return ret 