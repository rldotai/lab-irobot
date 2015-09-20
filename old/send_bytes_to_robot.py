"""
A quick program that sends the bytes from the command line to the iRobot Create

Usage:
	$ python send_bytes_to_robot.py <byte> [, <byte>, ...]
"""

import array
import numpy as np 
import select
import serial
import struct
import sys
import time

from time import sleep

SERIAL_PARAMS = {"baudrate":    57600,
				 "timeout": 0,
				 "parity": serial.PARITY_NONE,
				 "bytesize":serial.EIGHTBITS}


def openPort(portname, configDct):
	""" Open a port with the requested properties, return a pyserial object """
	try:
		ser = serial.Serial(portname, **configDct)
		# The below might not be necessary on some platforms
		ser.setRTS(0)
		time.sleep(0.25)
		ser.setRTS(1)
		time.sleep(0.5)
		ser.flushOutput()
		time.sleep(0.25)
	except Exception as e:
		print(e)
		ser = None

	return ser

def sendCmd(ser, cmdLst):
	tmp = struct.pack('B'*len(cmdLst), *cmdLst)
	try:
		sent = ser.write(tmp)
		ser.flush()
		return sent
	except Exception as e:
		print(e)

if __name__ == "__main__":
	if len(sys.argv) < 2: 
		print("You need to specify a serial port and some bytes to send")
		exit()

	try:
		# Get the port name
		port = sys.argv[1].strip()
		# Get byte values
		byteLst = [int(i) for i in sys.argv[2:]] # Get packet ID codes
		# Open the serial port
		ser  = openPort(port, SERIAL_PARAMS)
		# Send the bytes
		sendCmd(ser, byteLst)
		sleep(0.25)

	except Exception as e:
		print(e)
		raise e

	finally:
		ser.close()

