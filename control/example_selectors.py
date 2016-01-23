"""
An example use of the `controller.py` module, with selectors.
"""
from controller import *
import selectors

def gen_queue(parser):
    """Read from the packet parser as a generator."""
    lst = parser.buffer
    while True:
        if lst:
            yield lst.pop(0)
        else:
            yield None


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

        sel = selectors.DefaultSelector()
        sel.register(robot.ser, selectors.EVENT_READ)
        gen = gen_queue(pp.buffer)
        while True:
            events = sel.select()
            data = robot.ser.read() # as a generator...
            # print(ready, ord(data))
            pp.input(data)
            pkt = next(gen)
            if pkt:
                print("Praise Thor! The generator works!")
                print(pkt)

    except KeyboardInterrupt:
        print('\nReceived KeyboardInterrupt, exiting')
    finally:
        print("Shutting down robot and closing serial port...")
        robot.shutdown()


if __name__ == "__main__":
    port_name = '/dev/ttyUSB0'
    pkt_ids = [21, 22, 23, 24, 25, 26] # battery information
    main(port_name, pkt_ids)