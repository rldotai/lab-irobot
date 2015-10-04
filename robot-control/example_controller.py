"""
An example use of the `controller.py` module.
"""
from controller import *


def main(port, sensor_ids):
    # Open the serial port
    try:
        print("Opening port at:", port)
        robot = Controller(port, create.SERIAL_PARAMS)
    except Exception as e:
        raise(e)

    try:
        # Set mode to passive
        robot.mode_passive()

        # Set mode to full
        robot.mode_full()

        # Request sensor data and set up handler
        pp = csp3(sensor_ids)
        robot.request_stream(*sensor_ids)

        # Testing -- MODIFY
        # requesting a stream should return a generator?
        # or some other way of making it nonblocking...
        fd = robot.ser.fd 
        while True:
            ready, *_ = select.select([fd], [], [], 5)
            data = robot.ser.read() # as a generator...
            # print(ready, ord(data))
            pp.input(data)
    except KeyboardInterrupt:
        print('\nReceived KeyboardInterrupt, exiting')
    finally:
        print("Shutting down robot and closing serial port...")
        robot.shutdown()

if __name__ == "__main__":
    port_name = '/dev/ttyUSB0'
    pkt_ids = [21, 22, 23, 24, 25, 26] # battery information
    main(port_name, pkt_ids)