import math
import random
import pyrtl
from pyrtl import *

def pool_top(start, pool_en, vecs, nvecs, matrix_size, pool_size):
	with conditional_assignment:
		with pool_en: #perform pooling
			output |= full_pool(start, vecs, nvecs, matrix_size, pool_size)
		with otherwise: #perform normalization
			output |= normalization(start, vecs, nvecs, matrix_size)
	return output, nvecs #output = register list? or wire? nvecs should be updated to reflect new size if pooling occured
'''
Compares two values and returns MAX ONLY
'''
def bit_compare(in0, in1):
	out = pyrtl.WireVector(32)
	out_reg = pyrtl.Register(32)
	# with pyrtl.conditional_assignment:
	with in0 >= in1:
		out |= in0
	with in0 < in1:
		out |= in1
	out_reg.next <<= out
	return out_reg

'''
Performs MAX pooling of pool_in (a fixed size reg list)
modified to be generic to size. assuming padded with most negative number

returns 32b reg value. max of passed in list
'''
def line_pool(pool_in): 
	new_array = []
	if (len(pool_in) % 2 == 1):
		if len(pool_in) == 1:
			return pool_in[0]
		else:
			new_array.append(pool_in[-1])
	i = 0
	while i <= len(pool_in) - 2:
		new_array.append(bit_compare(pool_in[i], pool_in[i+1]))
		i += 2
	if len(pool_in) == 2:
		return bit_compare(pool_in[0], pool_in[1])
	return line_pool(new_array)

'''
start - initializes registers
vecs - input list of registers
nvecs - number of vectors
matrix_size - size of overall MMU
pool_size - self explanatory
# '''
def full_pool(start, vecs, nvecs, matrix_size, pool_size):
	# int_reg_lists = intermediate_pool(start, vecs, nvecs, matrix_size, pool_size)
	# final_reg_lists = final_pool(int_reg_lists, nvecs, matrix_size, pool_size)
	pass

'''
start - initializes registers
vecs - input list of registers
nvecs - number of vectors
matrix_size - size of overall MMU
pool_size - self explanatory
'''
def intermediate_pool(start, vecs, nvecs, vecs_length, matrix_size, pool_size):
	#wait for all vecs to shift in
	#perform parallel line pool on slices of reg_lists 
	#output line pool to final
	#creates Matrix_size x Matrix_size register array (line below)
	int_reg_lists = [[Register(32) for i in range(0, matrix_size)] for j in range(0, matrix_size)]
	line_pool_lists = [[Register(32) for i in range(0, matrix_size)] for j in range(0, matrix_size)]
	output_list = []
	temp1 = []
	temp2 = []

	shifting = Register(int(math.log(matrix_size, 2))) #max length of matrix_size
	pool_count = Register(int(math.log(matrix_size, 2)))
	setup = Register(1) #setup of reg lists
	pooling = Register(1)

	with conditional_assignment:
		with start:
			shifting.next |= 0
			setup.next |= 1
			pooling.next |= 0
			pool_count.next |= 0
		with setup == 1: #shift in phase vecs phase
			with shifting < matrix_size-1:
				shifting.next |= shifting + 1
				for vector in range(matrix_size-1, 0, -1): #reverse iteration of int_reg_lists until 2nd from top vector
					for index in range(0, matrix_size): #shifts down
						int_reg_lists[vector][index].next |= int_reg_lists[vector-1][index]
				vector = int_reg_lists[0]
				for index,reg in enumerate(vector): #shifts in new vals from veccs
					reg.next |= vecs[index] #Need to make sure to pad the rest of list with 0x80000000?
			with otherwise:
				setup.next |= 0
				pooling.next |= 1
				shifting.next |= 0
		with pooling == 1: #start line pooling phase
			pool_count.next |= pool_count + 1
			with pool_count == vecs_length-1:
				pooling.next |= 0
			for list_index in range(0, matrix_size):
				for reg_index in range(0, matrix_size-1): #shifts all left except for last one
					line_pool_lists[list_index][reg_index].next |= line_pool_lists[list_index][reg_index+1]
				line_pool_lists[list_index][-1].next |= int_reg_lists[list_index][0]
				for reg_index in range(0, matrix_size-1):
					int_reg_lists[list_index][reg_index].next |= int_reg_lists[list_index][reg_index+1]
				int_reg_lists[list_index][-1].next |= 0x80000000
			with shifting == pool_size-1: # add clear pool registers
				shifting.next |= 0
				temp1 = line_pool_lists[0] # a list
				temp2 = line_pool(temp1) # 1 value
				output_list.append(line_pool(line_pool_lists[0]))
				# for line_list in line_pool_lists:
					# output_list.append(line_pool(line_list))
			with otherwise:
				shifting.next |= shifting + 1
	return output_list, temp1, temp2, shifting, pooling, setup, pool_count, line_pool_lists #needs more outputs.


# def mux_pooling(start, vecs, vecs_length, nvecs, matrix_size):
# 	#NOTE: ONLY SUPPORTS 2 INPUTS. MAXPOOL AND PASSED IN VALUE. needs second layer of muxes for additional features
# 	busy = Register(1)
# 	constant_val = const(0x80000000, bitwidth = 32)
# 	counter = Register(math.log(matrix_size,2))
# 	mask = const(0xffffffff, bitwidth = 32)
# 	mux_control = Register(matrix_size)
# 	output_vecs = [Register(32) for i in range(0,matrix_size)]
# 	with conditional_assignment:
# 		with start:
# 			busy.next |= 1
# 			counter.next |= 0
# 			mux_control.next |= barrel.barrel_shifter(mask, bit_in = 0, direction = 0, shift_distance = vecs_length)
# 		with busy:\
# 			counter.next |= counter + 1
# 			with counter >= nvecs: #checks to see if all values have been passed in. 
# 				mux_control.next |= mask
# 			with otherwise: #can you pass a register into the barrel_shifter?
# 				mux_control.next |= barrel.barrel_shifter(mask, bit_in = 0, direction = 0, shift_distance = vecs_length)
# 			for i in range(0, matrix_size):
# 				output_vecs[i].next |= mux(mux_control[i], vecs[i], constant_val)

# 	return output_vecs


def final_pool():
	pass

'''
Rather than reusing full_pool, why not perform line_pool matrix_size times and then line_pool the result?.
It is a simple function to write and would keep the hardware separate. 
'''
def normalization(start, vecs, nvecs, matrix_size):
	pass



'''
SIMULATION AREA
'''

# intermediate_pool() test
# ----------------------------
reg_vec = [pyrtl.Register(32, 'reg_{}'.format(i)) for i in range(0, 8)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
start = pyrtl.Input(1, 'start')
start_reg = pyrtl.Register(1, 'start_reg')
nvecs = pyrtl.Register(4, 'nvecs')
nvecs.next <<= 8
mat_size = 8
pool_size = 2
vecs_length = 8
test_dict = {
		'input_0': 3,
		'input_1': 39,
		'input_2': 17,
		'input_3': 7,
		'input_4': 42,
		'input_5': 18,
		'input_6': 37,
		'input_7': 6,
		'start': 1
		}
output_orig = [pyrtl.Output(32, 'out_orig_{}'.format(i)) for i in range(0, 8)]
# output_int_pool= [pyrtl.Output(32, 'out_intpool_{}'.format(i)) for i in range(0, 8)]
# output_shifting = pyrtl.Output(3, 'shifting')

for index,reg in enumerate(reg_vec):
	reg.next <<= inputs[index]
	output_orig[index] <<= reg
int_pool_out, tempy, tempy2, shifting_wire, pooling_wire, setup_wire, pool_count, int_reg_lists = intermediate_pool(start, reg_vec, nvecs, vecs_length, mat_size, pool_size)
probe(shifting_wire, 'shifting_wire')
probe(pooling_wire, 'pooling_wire')
probe(setup_wire, 'setup_wire')
probe(pool_count, 'pool_count_wire')
for count, i in enumerate(int_pool_out):
	probe(i, 'out_{}'.format(count))
for count, i in enumerate(tempy):
	probe(i, 'tempy_{}'.format(count))
probe(tempy2, 'tempy2')
for countA, i in enumerate(int_reg_lists):
	for countB, j in enumerate(i):
		probe(j, 'int_reg_lists_{}_{}'.format(countA, countB))
# for index, reg in enumerate(output_int_pool):
	# reg <<= int_pool_out[index]
start_reg.next <<= start

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(40):
	sim.step(test_dict)
	if(cycle > 1):
		test_dict = {
			'input_0': 45,
			'input_1': 4,
			'input_2': 53,
			'input_3': 12,
			'input_4': 28,
			'input_5': 31,
			'input_6': 39,
			'input_7': 88,
			'start': 0
			}

# Now all we need to do is print the trace results to the screen. Here we use
# "render_trace" with some size information.
print('--- Simulation ---')
sim_trace.render_trace(symbol_len=5, segment_size=5)


# line_pool() test
# -------------------
# input_vec = [pyrtl.Register(32, 'reg_{}'.format(i)) for i in range(0, 8)]
# inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
# test_dict = {
# 		'input_0': 45,
# 		'input_1': 4,
# 		'input_2': 53,
# 		'input_3': 12,
# 		'input_4': 28,
# 		'input_5': 31,
# 		'input_6': 39,
# 		'input_7': 88,
# 		}
# output = pyrtl.Output(32, 'output')

# for index,reg in enumerate(input_vec):
# 	reg.next <<= inputs[index]
# output <<= line_pool(input_vec)

# sim_trace = pyrtl.SimulationTrace()
# sim = pyrtl.Simulation(tracer=sim_trace)

# for cycle in range(35):
# 	sim.step(test_dict)

# print('--- line_pool() simulation ---')
# sim_trace.render_trace(symbol_len=5, segment_size=5)


# end of line_pool() test
# ---------------------