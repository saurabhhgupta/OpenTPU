import pyrtl
from pyrtl import *
from pyrtl import rtllib
from pyrtl.rtllib import multipliers
from pyrtl.rtllib import adders
from pyrtl.rtllib import libutils


def maxBit(in0, in1):
	out = pyrtl.WireVector(32) # 32-bit wire - output
	out_reg = pyrtl.Register(32) # 32-bit register - output
	with pyrtl.conditional_assignment:
		with in0 >= in1: # check if in0 > or = to in1
			out |= in0 # if true, output is in0
		with in0 < in1: # otherwise
			out |= in1 # output is in1
	out_reg.next <<= out
	return out_reg # return the reg, not wire

def minBit(in0, in1):
	out = pyrtl.WireVector(32) # 32-bit wire - output
	out_reg = pyrtl.Register(32) # 32-bit register - output
	with pyrtl.conditional_assignment:
		with in0 < in1: # check if in0 < to in1
			out |= in0 # if true, output is in0
		with in0 >= in1: # otherwise
			out |= in1 # output is in1
	out_reg.next <<= out
	return out_reg # return the reg, not wire

# def maxComplex(pool_array):
# 	'''
# 	Re-used old maxPooling code: recursively splits the array in a
# 	binary tree like fashion to do comparisons with the maxSimple
# 	function (which makes comparisons with only two numbers)
# 	'''
# 	if (len(pool_in) == 1):
# 		return pool_in[0]
# 	elif (len(pool_in) == 2):
# 		return maxSimple(pool_in[0], pool_in[1])
# 	else:
# 		left_bit = maxComplex(pool_in[:len(pool_in) / 2])
# 		right_bit = maxComplex(pool_in[len(pool_in) / 2:])
# 	return maxSimple(left_bit, right_bit)


# def minComplex(pool_array):


# finalized up until this point
# -----------------------------------------------------------------

def linePool(line_in, used_width, pool_width): #OLD. UNUSED
	'''
	NEW SOLUTION with rotating matrix
	Assumptions:
	1) pool_in is an array of fixed size (width of mmu)
	2) matrix width is the amount used in pool_in
	3) pool width fits into the matrix width (used width) perfectly
	4) max/min bit can compare "x" bits

	Approach (ACTUAL APPROACH):
	1) perform initial line pool to create intermediate matrix which will be stored in buffer
	2) rotate and perform line pool again which will result in compressed, desired matrix
	'''
	index = 0
	line_out = []
	while index < (used_width - 1):
		pool_array = []
		i = 0
		for i in range(pool_width):
			pool_array.append(line_in[index + i])
		index += pool_width
		line_out.append(maxComplex(pool_array))
	return line_out

def maxPool(pool_in):	
	'''
	Inputs:
	pool_in - flattened matrix to be max pooled.

	Output:
	returns max value
	'''
	new_array = []
	if (len(pool_in) % 2 == 1): #if odd:
		if len(pool_in) == 1: #Edge Case: only 1 number in array
			return pool_in[0]
		else:
			new_array.append(pool_in[-1])
	i = 0
	while i < len(pool_in) - 2:
		new_array.append(maxBit(pool_in[i], pool_in[i+1]))
		i += 2
	if len(pool_in) == 2: #Size two array left
		return maxBit(pool_in[0], pool_in[1])
	return maxPool(new_array)


def maxPool_top(accum_out, matrix_size, pool_size):
	'''
	Input:
	matrix_width - width of overall matrix
	pool_width - width of pooling matrix
	waddr - write address
	raddr - read address

	Output:
	Returns resulting pooled matrix as pool_out
		- should this be stored in a given addr instead? In Unified buffer?
		- stored as 8bit? Need to truncate?

	how to clock this? registers?
	what exact format is accum_out? 2d array or flattened 2D array?
	'''
	level = 0
	while level < pool_size:
		x_index = 0
		pool_in = []
		while x_increment < pool_size:
			y_index = level*pool_size

			while y_increment < pool_size:
				too_add_val = [addr + y_increment] #shitty pseudo code
				#insert appending val to pool_in.
				y_increment+= 1
		pool_out.append(maxPool(pool_in)) #flattened matrix in order as if reading a book
		level += 1


# instantiate relu and set test inputs
din = []
din0 = pyrtl.Register(bitwidth=32, name='din0')
din0.next <<= 10
din1 = pyrtl.Register(bitwidth=32, name='din1')
din1.next <<= 12
din2 = pyrtl.Register(bitwidth=32, name='din2')
din2.next <<= 10
din3 = pyrtl.Register(bitwidth=32, name='din3')
din3.next <<= 12
din4 = pyrtl.Register(bitwidth=32, name='din4')
din4.next <<= 127
din5 = pyrtl.Register(bitwidth=32, name='din5')
din5.next <<= 12
din6 = pyrtl.Register(bitwidth=32, name='din6')
din6.next <<= 4
din7 = pyrtl.Register(bitwidth=32, name='din7')
din7.next <<= 12
din8 = pyrtl.Register(bitwidth=32, name='din8')
din8.next <<= 10


din.append(din0)
din.append(din1)
din.append(din2)
din.append(din3)
din.append(din4)
din.append(din5)
din.append(din6)
din.append(din7)
din.append(din8)


# print(maxNodeComparison(din4, din6))

dout = maxPool(din)
cmpr_out = pyrtl.Register(bitwidth=32, name='cmpr_out')
cmpr_out.next <<= dout 


# Simulate the instantiated design
sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)
for cycle in range(20):
	sim.step({})
sim_trace.render_trace()