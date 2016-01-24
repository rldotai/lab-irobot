"""
A simple UDP client example, to be used as a basis for more complicated
programs.

It connects once to a server (provided by `udp_server.py`) on the local machine
and then reads messages as they become available, using `select` to check for
new input.
"""
import json
import select
import socket
import time


PORT = 10000
HOST = socket.gethostname()


# udp socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

last = -1

try:
    # send a message so the server knows our address
    msg = b"hello"
    sock.sendto(msg, (HOST, PORT))
    while True:
        try:
            # use select to get input, if it's available
            (rlst, wlst, elst) = select.select([sock], [], [])
            if sock in rlst:
                # receive data from the socket
                reply, addr = sock.recvfrom(1024)
                # deserialize it from bytes
                data = json.loads(reply.decode('ascii'))
                print(data)

                # check message ordering
                count = data['count']
                if count != last + 1:
                    print("Received a message out of order!")
                last = count
        except socket.error as e:
            raise(e)
finally:
    # always close a socket when you're done with it
    sock.close()
