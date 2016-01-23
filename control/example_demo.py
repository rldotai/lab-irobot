"""
An example use of the `controller.py` module to run a builtin demo.
"""
from controller import *
import json
import selectors




if __name__ == "__main__":
    port = '/dev/ttyUSB0'
    
    # sensor_ids = [21, 22, 23, 24, 25, 26] # battery information
    sensor_ids = [27, 28, 29, 30, 31] # sensor information
    sensor_ids = [25, 26, 27, 28, 29, 30, 31] # battery information + sensors



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
        robot.run_demo(4)

        # Testing -- MODIFY
        # requesting a stream should return a generator?
        # or some other way of making it nonblocking...
        
        # Use `selectors` for IO readiness
        sel = selectors.DefaultSelector()
        sel.register(robot.ser, selectors.EVENT_READ)

        while True:
            events = sel.select()
            data = robot.ser.read()
            
            # Pass received data into the packet parser
            pp.input(data)

            # Check if a packet has been assembled by the parser
            if pp.buffer:
                dct = pp.buffer.pop(0)
                print(json.dumps(dct, indent=2))

    except KeyboardInterrupt:
        print('\nReceived KeyboardInterrupt, exiting')
    except Exception as e:
        raise(e)
    finally:
        print("Shutting down robot and closing serial port...")
        robot.stop_demo()
        robot.shutdown()