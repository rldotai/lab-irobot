"""
A simple UDP server example, to use as the basis for putting together more
complicated programs.

It can also be used for testing throughput/message ordering.
As `INTERVAL` gets closer to zero, more messages are sent, and the likelihood
that eventually one message gets dropped becomes higher and higher.
"""
import json
import select
import socket
import time


PORT = 10000
LOCALHOST = socket.gethostname()
INTERVAL = 0.5


# A simple counter generator
def gen_countup():
	x = 0
	while True:
		yield x
		x += 1
countup = gen_countup()

try:
	# udp socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind(('', PORT))
	print("Waiting on port:", PORT)

	# wait for another program to contact the server
	msg, addr = sock.recvfrom(1024)
	print("Connected to:", addr)
	while True:
		# build the data to send to the client, and convert it to bytes
		dct = {'count': next(countup), 'time': time.time()}
		data = bytes(json.dumps(dct), 'ascii')
		sock.sendto(data, addr)
		# sleep for a bit before sending the next message
		# time.sleep(INTERVAL)

finally:
    # always close a socket when you're done with it
	sock.close()