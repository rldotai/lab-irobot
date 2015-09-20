"""
Some easy to refer to (and also easy to import) opcode related information
for the iRobot Create.

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