"""
Program for displaying a readout of the Create's sensors.
"""


import select
import serial
import struct
import sys
import time


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
    """ Send a command, i.e., a list of bytes (as integers) to the robot."""
    tmp = struct.pack('B'*len(cmdLst), *cmdLst)
    try:
        sent = ser.write(tmp)
        ser.flush()
        return sent
    except Exception as e:
        print(e)


def requestStream(ser, sensorLst):
    """ A wrapper function for requesting a sensor stream of certain packets.
        sensorLst here is a list of integers corresponding to packets as in 
        the iRobot Create Open Interface documentation. 
    """
    length = len(sensorLst)
    cmdLst = [OP_STREAM, length] + sensorLst
    ret = sendCmd(ser, cmdLst)
    return ret

def makeBytes(lst):
    """ A quick way to pack a list of byte-long objects into a byte struct """
    return struct.pack("B"*len(lst), *lst)