import math
# import io
import random
import pyrtl
from pyrtl import *

'''
Compares two values and returns MAX ONLY
'''
def bit_compare(in0, in1):
	out = pyrtl.WireVector(32)
	with in0[-1] == 1:
		with in1[-1] == 0:
			out |= in1
		with otherwise:
			with in0 >= in1:
				out |= in0
			with otherwise:
				out |= in1
	with in1[-1] == 1:
		out |= in0
	with otherwise:
		with in0 >= in1:
			out |= in0
		with otherwise:
			out |= in1
	return out
  	# with pyrtl.conditional_assignment:
	# with in0 >= in1:
	# 	out |= in0
	# with pyrtl.otherwise:
	# 	out |= in1
	# return out

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
	if len(pool_in) == 2:
		return bit_compare(pool_in[0], pool_in[1])
	while i <= len(pool_in) - 2:
		new_array.append(bit_compare(pool_in[i], pool_in[i + 1]))
		i += 2
	return line_pool(new_array)


'''
start - initializes registers
vecs - input list of registers
nvecs - number of vectors
matrix_size - size of overall MMU
pool_size - self explanatory
'''
def final_pool(start, vecs, nvecs, vecs_length, matrix_size, pool_size):
	int_reg_lists = [[Register(32) for i in range(0, matrix_size)] for j in range(0, matrix_size)]
	line_pool_lists = [[Register(32) for i in range(0, matrix_size)] for j in range(0, matrix_size)]
	final_pool_list = []

	shifting = Register(int(math.log(matrix_size, 2)) + 1) #max length of matrix_size
	pool_count = Register(int(math.log(matrix_size, 2))+1)
	setup = Register(1) #setup of reg lists
	pooling = Register(1)
	clear = Register(1)

	with conditional_assignment:
		with start:
			shifting.next |= 0
			setup.next |= 1
			pooling.next |= 0
			pool_count.next |= 0
			clear.next |= 0 #clearing line_pool registers phase in pooling state. 
		with setup == 1: #shift in phase vecs phase
			with shifting < matrix_size-1:
				shifting.next |= shifting + 1
				for vector in range(matrix_size-1, 0, -1): #reverse iteration of int_reg_lists until 2nd from top vector
					for index in range(0, matrix_size): #shifts down
						int_reg_lists[vector][index].next |= int_reg_lists[vector-1][index]
				vector = int_reg_lists[0]
				for index,reg in enumerate(vector): #shifts in new vals from vecs
					reg.next |= vecs[index] #Need to make sure to pad the rest of list with 0x80000000?
			with otherwise:
				setup.next |= 0
				pooling.next |= 1
				shifting.next |= 0
				clear.next |= 0
		with pooling == 1: #start line pooling phase
			with clear:
				clear.next |= 0
				for vector in line_pool_lists:
					for reg in vector:
						reg.next |= 0x80000000
						# reg.next |= 0
			with otherwise:
				with pool_count == pool_size:
					pool_count.next |= 0
					clear.next |= 1
					# single_list = line_pool_lists[0] # a list. need to change back to for loop
					# pooled_value = line_pool(single_list) # 1 value
					for i in line_pool_lists:
						final_pool_list.append(line_pool(i))
				with shifting == vecs_length:
					pooling.next |= 0
				with pool_count < pool_size:
					for list_index in range(0, matrix_size):
						for reg_index in range(0, matrix_size-1): #shifts all left except for last one
							line_pool_lists[list_index][reg_index].next |= line_pool_lists[list_index][reg_index+1]
						line_pool_lists[list_index][-1].next |= int_reg_lists[list_index][0]
						for reg_index in range(0, matrix_size-1):
							int_reg_lists[list_index][reg_index].next |= int_reg_lists[list_index][reg_index+1]
						int_reg_lists[list_index][-1].next |= 0x80000000
					shifting.next |= shifting + 1
					pool_count.next |= pool_count + 1
	return concat_list(final_pool_list), shifting, pooling, setup, pool_count, int_reg_lists #needs more outputs.


# pyrtl.set_debug_mode()

reg_vec = [pyrtl.Register(32, 'reg_{}'.format(i)) for i in range(0, 9)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 9)]
start = pyrtl.Input(1, 'start')
start_reg = pyrtl.Register(1, 'start_reg')
nvecs = pyrtl.Register(5, 'nvecs')
nvecs.next <<= 9
mat_size = 9
pool_size = 9
vecs_length = 9
test_dict = {
		'input_0': 0x80000001,
		'input_1': 0x80000000,
		'input_2': 0x35,
		'input_3': 0xc,
		'input_4': 0x1c,
		'input_5': 0x1f,
		'input_6': 0x27,
		'input_7': 0x58,
		'input_8': 0x00,
		'start': 1
		}
output_orig = [pyrtl.Output(32, 'out_orig_{}'.format(i)) for i in range(0, 9)]

for index,reg in enumerate(reg_vec):
	reg.next <<= inputs[index]
	output_orig[index] <<= reg
final_list, shifting_wire, pooling_wire, setup_wire, pool_count, int_reg_lists = final_pool(start, reg_vec, nvecs, vecs_length, mat_size, pool_size)
probe(shifting_wire, 'shifting_wire')
probe(pooling_wire, 'pooling_wire')
probe(setup_wire, 'setup_wire')
probe(pool_count, 'pool_count_wire')
for count, i in enumerate(single_list):
	probe(i, 'single_list_{}'.format(count))
for count_1, vector in enumerate(int_reg_lists):
	for count_2, i in enumerate(vector):
		probe(i, 'int_reg_lists_{}_{}'.format(count_1, count_2))
probe(pooled_value, 'pooled_value')

start_reg.next <<= start

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(50):
	sim.step(test_dict)
	if(cycle > 1 and cycle < 4):
		test_dict = {
			'input_0': 0x80000001,
			'input_1': 0x80000000,
			'input_2': 0x35,
			'input_3': 0xc,
			'input_4': 0x1c,
			'input_5': 0x1f,
			'input_6': 0x27,
			'input_7': 0x58,
			'input_8': 0x00,
			'start': 0
			}
	if(cycle > 5):
		test_dict = {
			'input_0': 1,
			'input_1': 2,
			'input_2': 3,
			'input_3': 4,
			'input_4': 5,
			'input_5': 6,
			'input_6': 7,
			'input_7': 8,
			'input_8': 9,
			'start': 0
			}

print('--- Simulation ---')
sim_trace.render_trace(symbol_len=5, segment_size=5)

# pyrtl.working_block().sanity_check()
# pyrtl.passes._remove_unused_wires(pyrtl.working_block())  # so that trivial_graph() will work

# print("--- Trivial Graph Format  ---")
# with io.StringIO() as tgf:
#     pyrtl.output_to_trivialgraph(tgf)
#     print(tgf.getvalue())