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
	$ python handler.py <port_name>

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
"""

import array
import numpy as np 
import select
import serial
import struct
import sys
import time

from time import sleep

import PacketData # Contains information about the various packets and their codes

# Neat idea: specify the opcode followed by the keyword arguments
# needed so that a function factory can make easily used functions
# for each command that you want to send to the Create

# Good Idea: Put opcodes in a dictionary...

_PRINT_DEBUG = True 
# Debug print statement ...
if _PRINT_DEBUG:
	def debug(*args, **kwargs):
		print("[DEBUG]: ", end="")
		print(*args, **kwargs)
else:
	def debug(*args, **kwargs):
		pass 

def since():
	""" A generator that yields the time in between successive calls """
	toc = time.time()
	while True:
		tic = time.time()
		yield (tic - toc) 
		toc = tic

OP_PASSIVE = 128
OP_CONTROL = 130
OP_FULL = 132

OP_BAUD = 129

OP_STREAM = 148
OP_PAUSE  = 150
OP_QUERY  = 142
OP_QUERY_LIST = 149


SERIAL_PARAMS = {"baudrate":    57600,
				 "timeout": 0,
				 "parity": serial.PARITY_NONE,
				 "bytesize":serial.EIGHTBITS}


def openPort(portname, configDct):
	""" Open a port with the requested properties, return a pyserial object """
	try:
		debug("Opening port: {}".format(portname))
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
	""" Send a series of bytes (in list form) to the serial port """
	tmp = struct.pack('B'*len(cmdLst), *cmdLst)
	try:
		debug("Sending: {}".format(tmp))
		sent = ser.write(tmp)
		ser.flush()
		return sent
	except Exception as e:
		print(e)

def setModePassive(ser):
	ret = sendCmd(ser, [OP_PASSIVE])
	return ret

def setModeFull(ser):
	ret = sendCmd(ser, [OP_FULL])
	return ret

def pauseStream(ser):
	ret = sendCmd(ser, [OP_PAUSE, 0])
	return ret

def requestStream(ser, sensorLst):
	length = len(sensorLst)
	cmdLst = [OP_STREAM, length] + sensorLst
	debug(cmdLst)
	ret = sendCmd(ser, cmdLst)
	return ret

def shutdownRobot(ser):
	""" Shuts down a robot that is using the "ser" Serial object """
	debug("Shutting Down Robot")
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
	""" Class for handling streaming sensor data from the iRobot Create """
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
				self.lastPacket = self.wrapper(self.curPacket)
				print("\nPacket:", self.lastPacket)

			else:
				print("Misaligned packet:", self.curPacket)

			# Either way, reset self.curPacket
			self.curPacket		= []
			self.count 			= 0
			self.checksum		= 0
			self.state 			= csp3.WAIT_HEADER


	def wrapper(self, packet): 
		""" Assuming the packet is well formed, convert it to bytes,
			and then format according to the specification """
		# Get the data bytes from the packet, via numpy tricks
		tmp = np.array(packet)[~self.nonDataMask] # Not optimal!
		tmp = struct.pack("B"*self.numBytes, *tmp)
		ret = struct.unpack(self.dataFormat, tmp)
		#print(next(self.wrapper_timer))
		return ret
		

	def printParams(self):
		""" Print parameters (and much else) for the csp3 packet handler """
		print("Total size:",  self.totalSize)
		print("Packet info:\n", "\n".join([str(i) for i in self.packetInfo]))
		print("sizeLst:", self.sizeLst)
		print("idIx:", self.idIx)
		print("nonDataIx", self.nonDataIx)
		print("nonDataMask", self.nonDataMask)
		print("packetCheck", self.packetCheck)
		print("dataIx", self.dataIx)
		print("packetTypes", self.packetTypes)
		print("dataFormat", self.dataFormat)



def main():
	# Specify the port from command line
	port = sys.argv[1]  
	ser  = openPort(port, SERIAL_PARAMS)
	fd   = ser.fileno() # Not used in this version
	debug(port)
	try:
		# Set up the robot
		setModePassive(ser)

		# Set up select()
		ser.nonblocking() # Make the serial port non-blocking
		fd = ser.fileno()

		#setModeFull(ser)
		packets = [int(i) for i in sys.argv[2:]] # Get packet ID codes
		handler = csp3(packets) # Set up the handler
		handler.printParams()   # Print some information about handler
		requestStream(ser, packets) # Request the stream of above packets

		# Time the code why not?
		loop_timer = since()
		while True:
			select.select([fd], [], [], 5) 
			data = ord(ser.read(1)) # Get the data in integer form
			handler.inputByte(data)	# Pass the data to the handler
			#print(next(loop_timer))
	
	# Perform exceptional exception handling
	except Exception as e:
		print(e)

	# Ensure that the robot is shut down properly
	finally:
		shutdownRobot(ser)
		ser.close()
		sleep(0.5) # Superstition, because OS X serial hangs require a reboot 



if __name__ == "__main__":
	main()