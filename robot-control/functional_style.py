"""
Functions for controlling the iRobot Create.
"""
import select
import struct

import serial
from time import sleep, time 

import create_v1 as create 
from csp3 import csp3


def open_port(port, params):
    try:
        ser = serial.Serial(port, **params)
        ser.setRTS(0)
        sleep(0.25)
        ser.setRTS(1)
        sleep(0.25)
        ser.flushOutput()
        sleep(0.25)
    except Exception as e:
        ser = None
        raise(e)
    return ser 

def shutdown(ser):
    try:
        pause_stream(ser)
        sleep(1.5)
        ser.flushOutput()
        mode_passive(ser)
        sleep(1.5)
    except Exception as e:
        ser.flush()
        ser.flushOutput()
        ser.flushInput()
        ser.close()
        raise(e)

def send_cmd(ser, lst):
    cmd = struct.pack('B'*len(lst), *lst)
    try:
        sent = ser.write(cmd)
        ser.flush()
        return sent
    except Exception as e:
        raise(e)

def mode_full(ser):
    pass

def mode_passive(ser):
    return send_cmd(ser, [create.OP_PASSIVE])

def pause_stream(ser):
    return send_cmd(ser, [create.OP_PAUSE, 0])

def request_stream(ser, sensor_ids):
    length = len(sensor_ids)
    cmd_lst = [create.OP_STREAM, length] + sensor_ids
    return send_cmd(ser, cmd_lst)

def soft_reset(ser):
    pass