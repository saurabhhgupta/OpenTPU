from pyrtl import *
from pyrtl import rtllib
from pyrtl.rtllib import multipliers

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

def maxPooling(pool_in):
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
	length = len(pool_in)
	new_array = [int((length+1)/2)]
	if (length % 2 == 1): #if odd:
		if length == 1: #Edge Case: only 1 number in array
			return pool_in[0]
		else:
			new_array[-1] = pool_in[-1]
	i = 0
	while i < length - 2:
		new_array[i] = maxPooling(pool_in[i], pool_in[i+1])
		i += 2
	if length == 2: #Size two array left
		return maxBit(pool_in[0], pool_in[1])
	return maxPooling(new_array)

def averagePooling():
	'''
	Approach for avg pooling:
	'''


def minPooling():
	'''
	Approach for min pooling:
	1) Verify that input is 1 bit
	2) If 2 bits, compare the bits
	3) If 3 or more bits, recursively run min pooling
	'''
	if (len(pool_in) == 1):
		return pool_in[0]
	elif (len(pool_in) == 2):
		return minBit(pool_in[0], pool_in[1])
	else:
		left_bit = minPooling(pool_in[:len(pool_in) / 2])
		right_bit = minPooling(pool_in[len(pool_in) / 2:])
		return minBit(left_bit, right_bit)


# Simulate the instantiated design
sim_trace = pyrtl.SimulateTrace()
sim = pyrtl.Simulation(tracer=sim_trace)
for cycle in range(35):
	sim.step({})
sim_trace.render_trace()