# Overview

Here are some scripts I found useful for doing one-off tasks with the iRobot Create. 
They're in python3, which is not as fast as C but is generally faster to work
with. 
I've got some similar programs in C, but they're less tested, and I am not really sure that providing metaprograms to generate handlers is really in the spirit of helpful, shareable scripts.

## Requirements

* Python 3 (ideally, Python 3.4)
* PySerial (specifically, a version which works with Python 3)
    - Fairly easy to get via `pip install pyserial` if not installed, although you might have to specify which python version you're using.
* (If on a Mac) some sort of usb-serial port driver e.g. the one from Prolific.

## Usage

The scripts work by specifying a serial port (such as `/dev/ttyUSB0`) and then a series of integers corresponding to packet IDs (as specified in the iRobot Create Open Interface manual).
I recommend using the `select_handler.py` version, because it's more self-contained, and likely faster.

Example:

```bash
python3 select_handler.py /dev/ttyUSB0 24 25 26
```
