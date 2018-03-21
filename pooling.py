import pyrtl
import math
from pyrtl import *
from pyrtl import rtllib
from pyrtl.rtllib import multipliers
from pyrtl.rtllib import adders
from pyrtl.rtllib import libutils


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
def intermediate_pool(start, vecs, nvecs, vecs_length, matrix_size, pool_size):
	int_reg_lists = [[Register(32) for i in range(0, matrix_size)] for j in range(0, matrix_size)]
	line_pool_lists = [[Register(32) for i in range(0, matrix_size)] for j in range(0, matrix_size)]

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
					single_list = line_pool_lists[0] # a list. need to change back to for loop
					pooled_value = line_pool(single_list) # 1 value
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
	return single_list, pooled_value, shifting, pooling, setup, pool_count, int_reg_lists #needs more outputs.
