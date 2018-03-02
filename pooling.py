import pyrtl
from pyrtl import *
from pyrtl import rtllib
from pyrtl.rtllib import multipliers
from pyrtl.rtllib import adders
from pyrtl.rtllib import libutils


def maxSimple(in0, in1):
	out = pyrtl.WireVector(32) # 32-bit wire - output
	out_reg = pyrtl.Register(32) # 32-bit register - output
	with pyrtl.conditional_assignment:
		with in0 >= in1: # check if in0 > or = to in1
			out |= in0 # if true, output is in0
		with in0 < in1: # otherwise
			out |= in1 # output is in1
	out_reg.next <<= out
	return out_reg # return the reg, not wire

def minSimple(in0, in1):
	out = pyrtl.WireVector(32) # 32-bit wire - output
	out_reg = pyrtl.Register(32) # 32-bit register - output
	with pyrtl.conditional_assignment:
		with in0 < in1: # check if in0 < to in1
			out |= in0 # if true, output is in0
		with in0 >= in1: # otherwise
			out |= in1 # output is in1
	out_reg.next <<= out
	return out_reg # return the reg, not wire

def maxComplex(pool_array):
	'''
	Re-used old maxPooling code: recursively splits the array in a
	binary tree like fashion to do comparisons with the maxSimple
	function
	'''
	if (len(pool_in) == 1):
		return pool_in[0]
	elif (len(pool_in) == 2):
		return maxSimple(pool_in[0], pool_in[1])
	else:
		left_bit = maxComplex(pool_in[:len(pool_in) / 2])
		right_bit = maxComplex(pool_in[len(pool_in) / 2:])
	return maxSimple(left_bit, right_bit)


def minComplex(pool_array):


# finalized up until this point
# -----------------------------------------------------------------

def linePool(line_in, used_width, pool_width):
	'''
	Approach for max pooling:
	1) Verify that input is 1 bit
	2) If 2 bits, compare the bits
	3) If 3 or more bits, recursively run max pooling
	if (len(pool_in) == 1):
		return pool_in[0]
	elif (len(pool_in) == 2):
		return maxBit(pool_in[0], pool_in[1])
	else:
		left_bit = maxPooling(pool_in[:len(pool_in) / 2])
		right_bit = maxPooling(pool_in[len(pool_in) / 2:])
		return maxBit(left_bit, right_bit)
	'''
	# PREVIOUSLY WORKING SOLUTION
	# new_array = []
	# if (len(pool_in) % 2 == 1): #if odd:
	# 	if len(pool_in) == 1: #Edge Case: only 1 number in array
	# 		return pool_in[0]
	# 	else:
	# 		new_array.append(pool_in[-1])
	# i = 0
	# while i < len(pool_in) - 2:
	# 	new_array.append(maxBit(pool_in[i], pool_in[i+1]))
	# 	i += 2
	# if length == 2: #Size two array left
	# 	return maxBit(pool_in[0], pool_in[1])
	# return maxPooling(new_array)
	'''
	NEW SOLUTION with rotating matrix
	Assumptions:
	1) pool_in is an array of fixed size (width of mmu)
	2) matrix width is the amount used in pool_in
	3) pool width fits into the matrix width (used width) perfectly
	4) max/min bit can compare "x" bits
	'''
	'''
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

def maxPool(input_addr_list, intermediate_addr_list, result_addr_list, pool_width):
	'''
	input_addr_list: list of addresses for first array (FIFO)
	intermediate_addr_list: list of addresses for line_out   
	'''
	result = []
	used_width = len(input_addr_list)
	current_line = []
	output_line = []
	i = 0
	for i in range(len(input_addr_list)):
		#initial loop to create intermediate matrix
		current_line = read_data(input_addr_list[i]) #replace with correct syntax for addressing
		output_line = linePool(current_line)
		write_data(intermediate_addr_list[i])
	i = 0
	for i in range(used_width/pool_width):
		'''
		second loop to complete pooling of array.
		should write to resulting addr list in correct orientation
		'''
		intermediate_array = []
		j = 0
		for j in range(used_width): #create array to pass into linePool
			intermediate_array.append(read_data(intermediate_addr_list[j][i]))
		output_line = linePool(intermediate_array)
		write_data(result_addr_list[i])


def minPooling(pool_in):
	'''
	Approach for min pooling:
	1) Verify that input is 1 bit
	2) If 2 bits, compare the bits
	3) If 3 or more bits, recursively run min pooling
	'''
	# if (len(pool_in) == 1):
	# 	return pool_in[0]
	# elif (len(pool_in) == 2):
	# 	return minBit(pool_in[0], pool_in[1])
	# else:
	# 	left_bit = minPooling(pool_in[:len(pool_in) / 2])
	# 	right_bit = minPooling(pool_in[len(pool_in) / 2:])
	# 	return minBit(left_bit, right_bit)

	length = len(pool_in)
	new_array = []
	if (length % 2 == 1): #if odd:
		if length == 1: #Edge Case: only 1 number in array
			return pool_in[0]
		else:
			new_array.append(pool_in[-1])
	i = 0
	while i < length - 2:
		new_array.append(minBit(pool_in[i], pool_in[i+1]))
		i += 2
	if length == 2: #Size two array left
		return minBit(pool_in[0], pool_in[1])
	return minPooling(new_array)


# def maxNodeComparison(node_a, node_b):
# 	# a, b = libutils.match_bitwidth(node_a, node_b)
# 	zero = pyrtl.Register(1)
# 	one = pyrtl.Register(16)ls

# 	zero <<= 0
# 	one <<= 1
# 	reg_inv_b = pyrtl.Register(~node_b)
# 	reg_inv_b = kogge_stone(one, reg_inv_b)
# 	reg_inv_b = kogge_stone(node_a, reg_inv_b)
# 	with pyrtl.conditional_assignment:
# 		with reg_inv_b[0] == zero:
# 			return node_a
# 		with pyrtl.otherwise:
# 			return node_b





# def treeCompare(node_one, node_two):
# 	odd_reg = pyrtl.Register(bitwidth=16, name=odd_reg)






# def maxPool(pool_in, width):
# 	# width is the "used" portion of pool_in (how much of pool_in is actually used)
# 	# pool_in is 256-bit wide array
	# carry_save = pyrtl.Register(bitwidth=16, name'carry_save')













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

dout = maxPooling(din)
cmpr_out = pyrtl.Register(bitwidth=32, name='cmpr_out')
cmpr_out.next <<= dout 


# Simulate the instantiated design
sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)
for cycle in range(20):
	sim.step({})
sim_trace.render_trace()