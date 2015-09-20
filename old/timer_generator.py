#!/python3
""" Timing code with a generator. A quick test suggests that they are very close """

import time

def since():
	toc = time.time()
	while True:
		tic = time.time()
		yield (tic - toc) 
		toc = tic

def test(n=10, delay=0.001):
	s = since()
	gen_lst  = []
	base_lst = []

	# For the generator
	for i in range(n):
		gen_lst.append(next(s))
		time.sleep(delay)

	# Now for the base case
	toc = time.time()
	for i in range(n):
		tic = time.time()
		base_lst.append(tic-toc)
		toc = tic 
		time.sleep(delay)

	# Comparison:

	print("Base Case\t With generator\t Difference")
	for i in range(n):
		diff = base_lst[i] - gen_lst[i]
		print("{0:3.7f}\t {1:3.7f}\t {2:3.7f}".format(base_lst[i], gen_lst[i], diff))
