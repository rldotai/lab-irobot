"""
A program (based off of my Python Create Serial Packet Processor) which 
can be customized fairly quickly in order to get the robot to do different things.

In its current form, the program: 

0. Takes command line arguments specifying a port and packet codes 
1. Opens a serial port to communicate with an iRobot Create 
2. Sets up a handler specific to the packet codes (from command line args)
3. Requests a stream from the iRobot Create containing those packets
4. Prints the value of those packets until program is terminated (e.g., Ctrl-C)

Usage:
	$ python handler.py <port_name> [packet_id, packet_id, ...]

Examples:

# Displays the infrared sensors at the front of the robot 
	$ python handler.py /dev/ttyUSB0 28 29 30 31

# Displays information about the iRobot Create's battery
	$ python handler.py /dev/ttyUSB0 24 25 26

It uses select() to wait for input from the Create, reading a single byte at a
time, although code exists to make use of serial.Serial.numWait()

Tested with Python 3.4 on Ubuntu 12.04, it has fairly stable processing time 
for the packets, although it is far from optimized. 
Packets should arrive every 0.015 seconds, testing on my desktop has +/- 0.004s
deviation from that ideal. 

Changes have been made to bring all the code into a single file, for easier
distribution.
"""

import numpy as np 
import select
import serial
import struct
import sys
import time

from time import sleep

# Opcodes for communicating w/ the robot (this might be better as a dictionary)
OP_PASSIVE = 128 		# Set the robot's mode to passive
OP_CONTROL = 130 		# Set the robot's mode to "safe"
OP_FULL = 132 			# Set the robot's mode to "full"
OP_BAUD = 129 			# Change the robot's baud rate
OP_STREAM = 148 		# Request a stream of sensor data from the robot
OP_PAUSE  = 150 		# Pause (or unpause) the robot's sensor data stream
OP_QUERY  = 142 		# Request the value for a single sensor
OP_QUERY_LIST = 149 	# Request the values for a list of sensors


# The parameters for opening the serial port
SERIAL_PARAMS = {"baudrate":    57600,
				 "timeout": 0,
				 "parity": serial.PARITY_NONE,
				 "bytesize":serial.EIGHTBITS}

# A dictionary for the types of packets the robot can send
PacketDct = \
{7: {'ValueRange': [0, 31],
  'dtype': 'B',
  'id': 7,
  'name': 'BumpsAndWheelDrops',
  'size': 1,
  'units': None},
 8: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 8,
  'name': 'Wall',
  'size': 1,
  'units': None},
 9: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 9,
  'name': 'CliffLeft',
  'size': 1,
  'units': None},
 10: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 10,
  'name': 'CliffFrontLeft',
  'size': 1,
  'units': None},
 11: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 11,
  'name': 'CliffFrontRight',
  'size': 1,
  'units': None},
 12: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 12,
  'name': 'CliffRight',
  'size': 1,
  'units': None},
 13: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 13,
  'name': 'VirtualWall',
  'size': 1,
  'units': None},
 14: {'ValueRange': [0, 31],
  'dtype': 'B',
  'id': 14,
  'name': 'Overcurrents',
  'size': 1,
  'units': None},
 15: {'ValueRange': [0, 0],
  'dtype': 'B',
  'id': 15,
  'name': 'Unused',
  'size': 1,
  'units': None},
 16: {'ValueRange': [0, 0],
  'dtype': 'B',
  'id': 16,
  'name': 'Unused',
  'size': 1,
  'units': None},
 17: {'ValueRange': [0, 255],
  'dtype': 'B',
  'id': 17,
  'name': 'IRByte',
  'size': 1,
  'units': None},
 18: {'ValueRange': [0, 15],
  'dtype': 'B',
  'id': 18,
  'name': 'Buttons',
  'size': 1,
  'units': None},
 19: {'ValueRange': [-32768, 32767],
  'dtype': 'h',
  'id': 19,
  'name': 'Distance',
  'size': 2,
  'units': None},
 20: {'ValueRange': [0, 5],
  'dtype': 'h',
  'id': 20,
  'name': 'Angle',
  'size': 2,
  'units': None},
 21: {'ValueRange': [0, 5],
  'dtype': 'B',
  'id': 21,
  'name': 'ChargingState',
  'size': 1,
  'units': None},
 22: {'ValueRange': [-32768, 32767],
  'dtype': 'H',
  'id': 22,
  'name': 'Voltage',
  'size': 2,
  'units': None},
 23: {'ValueRange': [-32768, 32767],
  'dtype': 'h',
  'id': 23,
  'name': 'Current',
  'size': 2,
  'units': None},
 24: {'ValueRange': [-128, 127],
  'dtype': 'b',
  'id': 24,
  'name': 'BatteryTemperature',
  'size': 1,
  'units': None},
 25: {'ValueRange': [0, 65535],
  'dtype': 'H',
  'id': 25,
  'name': 'BatteryCharge',
  'size': 2,
  'units': None},
 26: {'ValueRange': [0, 4095],
  'dtype': 'H',
  'id': 26,
  'name': 'BatteryCapacity',
  'size': 2,
  'units': None},
 27: {'ValueRange': [0, 4095],
  'dtype': 'H',
  'id': 27,
  'name': 'WallSignal',
  'size': 2,
  'units': None},
 28: {'ValueRange': [0, 4095],
  'dtype': 'H',
  'id': 28,
  'name': 'CliffLeftSignal',
  'size': 2,
  'units': None},
 29: {'ValueRange': [0, 4095],
  'dtype': 'H',
  'id': 29,
  'name': 'CliffFrontLeftSignal',
  'size': 2,
  'units': None},
 30: {'ValueRange': [0, 4095],
  'dtype': 'H',
  'id': 30,
  'name': 'CliffFrontRightSignal',
  'size': 2,
  'units': None},
 31: {'ValueRange': [0, 4095],
  'dtype': 'H',
  'id': 31,
  'name': 'CliffRightSignal',
  'size': 2,
  'units': None},
 32: {'ValueRange': [0, 31],
  'dtype': 'B',
  'id': 32,
  'name': 'UserDigitalInputs',
  'size': 1,
  'units': None},
 33: {'ValueRange': [0, 1023],
  'dtype': 'B',
  'id': 33,
  'name': 'UserAnalogInput',
  'size': 2,
  'units': None},
 34: {'ValueRange': [0, 3],
  'dtype': 'B',
  'id': 34,
  'name': 'ChargingSourcesAvailable',
  'size': 1,
  'units': None},
 35: {'ValueRange': [0, 3],
  'dtype': 'B',
  'id': 35,
  'name': 'OIMode',
  'size': 1,
  'units': None},
 36: {'ValueRange': [0, 15],
  'dtype': 'B',
  'id': 36,
  'name': 'SongNumber',
  'size': 1,
  'units': None},
 37: {'ValueRange': [0, 1],
  'dtype': 'B',
  'id': 37,
  'name': 'SongPlaying',
  'size': 1,
  'units': None},
 38: {'ValueRange': [0, 42],
  'dtype': 'B',
  'id': 38,
  'name': 'NumberOfStreamPackets',
  'size': 1,
  'units': None},
 39: {'ValueRange': [-500, 500],
  'dtype': 'h',
  'id': 39,
  'name': 'Velocity',
  'size': 2,
  'units': None},
 40: {'ValueRange': [-32768, 32767],
  'dtype': 'h',
  'id': 40,
  'name': 'Radius',
  'size': 2,
  'units': None},
 41: {'ValueRange': [-500, 500],
  'dtype': 'h',
  'id': 41,
  'name': 'RightVelocity',
  'size': 2,
  'units': None},
 42: {'ValueRange': [-500, 500],
  'dtype': 'h',
  'id': 42,
  'name': 'LeftVelocity',
  'size': 2,
  'units': None}}


############################### Actual Code ###################################

def since():
	""" A generator that yields the time in between successive calls """
	toc = time.time()
	while True:
		tic = time.time()
		yield (tic - toc) 
		toc = tic


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

def setModePassive(ser):
	""" A wrapper function for setting the robot's mode to passive."""
	ret = sendCmd(ser, [OP_PASSIVE])
	return ret

def setModeFull(ser):
	""" A wrapper function for setting the robot's mode to full."""
	ret = sendCmd(ser, [OP_FULL])
	return ret

def pauseStream(ser):
	""" A wrapper function for pausing the robot's sensor stream."""
	ret = sendCmd(ser, [OP_PAUSE, 0])
	return ret

def requestStream(ser, sensorLst):
	""" A wrapper function for requesting a sensor stream of certain packets.
		sensorLst here is a list of integers corresponding to packets as in 
		the iRobot Create Open Interface documentation. 
	"""
	length = len(sensorLst)
	cmdLst = [OP_STREAM, length] + sensorLst
	ret = sendCmd(ser, cmdLst)
	return ret

def shutdownRobot(ser):
	""" Shuts down a robot that is using the "ser" Serial object """
	print("Shutting down robot...")
	try:
		pauseStream(ser)
		sleep(1.5)
		ser.flushOutput()
		setModePassive(ser)
		sleep(1.5)
	except Exception as e:
		print(e)
		ser.flush()
		ser.flushOutput()
		ser.flushInput()
		ser.close()

def soft_reset(ser):
	""" 
	Invokes a soft reset of the iRobot Create.
	Useful when the Create has been switched to Passive Mode WHILE power is 
	available  -- it apparently only detects the rising current, so it might
	not actually begin charging.
	This is a somewhat undocumented feature (but is mentioned in the iRobot
	website support FAQ). It forces the robot to run its bootloader.
	
	IMPORTANT: 
	Do not send any data while the bootloader is running! 
	It takes ~3s, hence the time.sleep() in the function. 
	"""
	try:
		OP_SOFT_RESET = 7
		ret = sendCmd(ser, [OP_SOFT_RESET])
		sleep(3)
	except Exception as e:
		print(e)



def makeBytes(lst):
	""" A quick way to pack a list of byte-long objects into a byte struct """
	return struct.pack("B"*len(lst), *lst)



class csp3():
	""" A class that handles sensor data packets from robot."""
	PacketDct = PacketData.PacketDct
	WAIT_HEADER, IN_MSG = range(2)
	firstByte   = 19 # The byte signifying the start of a packet
	def __init__(self, sensorLst):
		self.packetInfo  = [csp3.PacketDct[i] for i in sensorLst]
		self.sizeLst     = np.array([i["size"] for i in self.packetInfo])
		self.numBytes    = np.sum(self.sizeLst)
		self.packetTypes = [i["dtype"] for i in self.packetInfo]
		self.dataFormat  = ">" + "".join(self.packetTypes)

		# Total size is based on the number of sensors, the size 
		# of the data from the sensors, plus 3 bytes for checking integrity
		self.totalSize  = len(sensorLst) + self.numBytes + 3

		# We want the indices where the sensor IDs (not their data) is located
		self.idIx        = np.cumsum(np.append(np.array(2), self.sizeLst + 1))[:-1]
		self.idMask      = np.in1d(np.arange(self.totalSize), self.idIx)
		# The indices where non-data (i.e., header, packet id, checksum) is located
		self.nonDataIx   = np.concatenate((np.array([0,1]), self.idIx, np.array([self.totalSize-1,])))
		# An index array for where non-data bytes appear
		self.nonDataMask = np.in1d(np.arange(self.totalSize - 1), self.nonDataIx)
		# The indices where data appears
		self.dataIx      = np.arange(self.totalSize - 1)[~self.nonDataMask]
		# Make an array of the checkbits, of size equal to total length of packet
		tmp 	 		 = np.zeros(self.totalSize)
		tmp[self.idMask] = np.array(sensorLst)
		self.packetCheck = tmp

		# Initialize the actual packet construction machinery
		self.lastPacket = []
		self.curPacket  = []
		self.count      = 0
		self.checksum   = 0
		self.state      = csp3.WAIT_HEADER

		# Debugging/Testing
		self.wrapper_timer = since()

	def printParams(self):
		""" Print parameters (and much else) for the csp3 packet handler """
		print("Total size:",  self.totalSize)
		#print("Packet info:", self.packetInfo)
		print("Packet info:\n", "\n".join([str(i) for i in self.packetInfo]))
		print("sizeLst:", self.sizeLst)
		print("idIx:", self.idIx)
		print("nonDataIx", self.nonDataIx)
		print("nonDataMask", self.nonDataMask)
		print("packetCheck", self.packetCheck)
		print("dataIx", self.dataIx)
		print("packetTypes", self.packetTypes)
		print("dataFormat", self.dataFormat)


	def inputByte(self, b):
		""" A reimplementation of inputLst for individual bytes

		:param b: The byte to handle 
		:type  b: int 

		It uses the same structure as inputLst but for single bytes. Some code has
		been skipped, because it is (currently) commented out anyways. 
		"""

		if (self.state == csp3.WAIT_HEADER):
			# It only matters if we're on the first byte
			if (b == csp3.firstByte):
				self.count += 1
				self.checksum += b 
				self.state = csp3.IN_MSG
				self.curPacket = [b]

		elif self.state == csp3.IN_MSG:
			self.curPacket.append(b)
			self.checksum += b
			self.count += 1

		else:
			raise RuntimeError("Handler is in unrecognized state:", self.state)

		# Once we have enough bytes, try to form a valid packet
		if self.count == self.totalSize:
			if ((self.checksum % 256) == 0):
				print("\nPacket:", self.wrapper(self.curPacket))
				self.lastPacket = self.curPacket.copy()
			else:
				print("Misaligned packet:", self.curPacket)

			# Either way, reset self.curPacket
			self.curPacket	= []
			self.count 			= 0
			self.checksum		= 0
			self.state 			= csp3.WAIT_HEADER


	def wrapper(self, packet): 
		""" Assuming the packet is well formed, convert it to bytes,
			and then format according to the specification """
		# Get the data bytes from the packet, via numpy tricks
		tmp = np.array(packet)[~self.nonDataMask] # Not good!
		tmp = struct.pack("B"*self.numBytes, *tmp)
		ret = struct.unpack(self.dataFormat, tmp)
		print(next(self.wrapper_timer))
		return ret
		



def main():
	# Specify the port from command line
	port = sys.argv[1]  
	ser  = openPort(port, SERIAL_PARAMS)
	fd   = ser.fileno() # Not used in this version
	print("Opening port at:", port)
	try:
		# Set up the robot (needs to be initialized as such to respond properly)
		setModePassive(ser) 

		# Set up select()
		ser.nonblocking() # Make the serial port non-blocking
		fd = ser.fileno()

		#setModeFull(ser) # Uncomment if you want to control the robot
		packets = [int(i) for i in sys.argv[2:]] # Get packet ID codes
		handler = csp3(packets) # Set up the handler
		handler.printParams()   # Print some information about handler
		requestStream(ser, packets) # Request the stream of above packets

		# Time the code why not?
		loop_timer = since()
		while True:
			select.select([fd], [], [], 5) 
			data = ord(ser.read(1))
			handler.inputByte(data)
			#print(next(loop_timer))
	
	# Perform exceptional exception handling
	except Exception as e:
		print(e) # So exceptional.

	# Ensure that the robot is shut down properly
	finally:
		shutdownRobot(ser)
		ser.close()
		sleep(0.5) # Superstition, because OS X serial hangs require a reboot 



if __name__ == "__main__":
	main()