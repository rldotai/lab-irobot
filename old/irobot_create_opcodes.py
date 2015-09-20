"""
Some easy to refer to (and also easy to import) opcode related information
for the iRobot Create.

The "irobot_create_opcodes.py" file (or "robocop") should make dealing with the
robot slightly easier.

Global data structures specified: 

For each opcode, this file should provide: 

*	A mapping between its numerical value and its name 

*	A mapping between its name and its numerical values

* [LOW PRIORITY] More detailed descriptions of the opcodes (like how many data
	bytes it needs)

OP_<OPCODE_NAME> = <num>

INFO_<OPCODE_NAME> = {"name": <OPCODE_NAME>,
											"opcode": <num>,
											"data_bytes", <num>,}

It may be useful to provide additional information in the INFO_<...> part


"""

def info(query):
	""" Maps opcode names to their byte value, or vice-versa

	:param query: The opcode name or byte value to return the information for.
	:type  query: str or int
	:returns:	int or str -- the corresponding byte value or name for the input
	:raises: 
	"""

	if type(query) == int:
		if query in byte_dct:
			return byte_dct[query]
		else:
			return ""

	elif type(query) == str:
		if query in name_dct:
			return name_dct[query]
		else:
			return -1

	else:
		raise RuntimeError("Query: {} not an opcode".format(query))


byte_dct = {
	128 : ""
	129 : ""
	130 : ""
	131 : ""
	132 : ""
	133 : ""
	134 : ""
	135 : ""
	136 : ""
	137 : ""
	138 : ""
	139 : ""
	140 : ""
	141 : ""
	142 : ""
	143 : ""
	144 : ""
	145 : ""
	146 : ""
	147 : ""
	148 : ""
	149 : ""
	150 : ""
	151 : ""
	152 : ""
	153 : ""
	154 : ""
	155 : ""
	156 : ""
	157 : ""
	158 : ""
}

opcode_dct= {
137: {"name" : "drive", "data_bytes":4,},
145: {"name": "drive_direct", "data_bytes":4 },
0: {"name": "", "data_bytes" : 0},
0: {"name": "", "data_bytes" : 0},
0: {"name": "", "data_bytes" : 0},
0: {"name": "", "data_bytes" : 0},
0: {"name": "", "data_bytes" : 0},
0: {"name": "", "data_bytes" : 0},
}

