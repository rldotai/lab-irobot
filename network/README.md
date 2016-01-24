There comes a time in every man's life where he must determine how best to control a fleet of robots over the Internet, or at least over his lab's Wi-Fi.

# Notes

Python is probably not ideal for the long-term goals of communicating with multiple sensors/robots, but it sufficies as a proof-of-concept.

Since we are using Python, however, it might be worthwhile to use the `socketserver` module instead of the raw sockets.

Further worth considering is whether/how to split up the communication-- should everything be allocated a single socket? Or should there be multiple sockets for different kinds of messages? e.g., TCP for parts where latency is irrelevant, UDP for sensor data stream, perhaps each sensor should have its own socket?

The question of "how to actually send the data" comes up as well-- how to serialize the messages, what to do when the messages are excessively long, etc.
Protobuf? JSON? Cap'n Proto? Apache Thrift?