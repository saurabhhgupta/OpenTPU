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
	with pyrtl.conditional_assignment:
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
	while i < len(pool_in) - 2:
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
'''
def full_pool(start, vecs, nvecs, matrix_size, pool_size):
	int_reg_lists = intermediate_pool(start, vecs, nvecs, matrix_size, pool_size)
	final_reg_lists = final_pool(int_reg_lists, nvecs, matrix_size, pool_size)


'''
start - initializes registers
vecs - input list of registers
nvecs - number of vectors
matrix_size - size of overall MMU
pool_size - self explanatory
'''
def intermediate_pool(start, vecs, nvecs, matrix_size, pool_size):
	#wait for all vecs to shift in
	#perform parallel line pool on slices of reg_lists 
	#output line pool to final
	int_reg_lists = [[Register(bitwidth = 32) for i range(0, matrix_size)] for j in range(0, matrix_size )] #creates Matrix_size x Matrix_size register array
	line_pool_lists = [[Register(bitwidth = 32) for i range(0, matrix_size)] for j in range(0, matrix_size )]
	output_list = []

	shifting = Register(math.log(matrix_size,2)) #max length of matrix_size
	setup = Register(1) #setup of reg lists
	pooling = Register(1)

	with conditional_assignment:
		with start:
			shifting.next |= 1
			setup.next |= 1
			pooling.next |= 0
		with setup == 1: #shift in phase vecs phase
			with shifting < nvecs:
				shifting.next |= shifting + 1
				for vector in range(matrix_size-1, 0, -1): #reverse iteration of int_reg_lists until 2nd from top vector
					for index in range(0, matrix_size): #shifts down
						int_reg_lists[vector][index].next |= int_reg_lists[vector-1][index]
				vector = int_reg_lists[0]
				for index,reg in enumerate(vector): #shifts in new vals from veccs
					reg |= vecs[index] #Need to make sure to pad the rest of list with 0x80000000?
			with shifting >= nvecs: #pad with negative number phase
				shifting.next |= shifting + 1
				for vector in range(matrix_size-1, 0, -1): #reverse iteration of int_reg_lists until 2nd from top vector
					for index in range(0, matrix_size): #shifts down
						int_reg_lists[vector][index].next |= int_reg_lists[vector-1][index]
				vector = int_reg_lists[0]
				for index,reg in enumerate(vector): #shifts in new vals from veccs
					reg |= 0x80000000 #most negative number 
					with shifting == matrix_size #2d register array full
						setup.next |= 0
						pooling.next |= 1
						shifting.next |= 0
		with pooling == 1: #start line pooling phase
			shifting.next |= shifting + 1
			for list_index in range(0, matrix_size):
				for reg_index in range(0, matrix_size-1): #shifts all left except for last one
					line_pool_lists[list_index][reg_index].next |= line_pool_lists[list_index][reg_index+1]
				line_pool_lists[list_index][-1].next |= int_reg_lists[list_index][0]
				for reg_index in range(0, matrix_size-1):
					int_reg_lists[list_index][reg_index].next |= int_reg_lists[list_index][reg_index+1]
				int_reg_lists[list_index][-1].next |= 0x80000000
			with shifting == pool_size:
				for line_list in line_pool_lists:
					output_list.append(line_pool(line_list))
	return output_list, #needs more outputs.

def final_pool():
	pass

'''
Rather than reusing full_pool, why not perform line_pool matrix_size times and then line_pool the result?.
It is a simple function to write and would keep the hardware separate. 
'''
def normalization(start, vecs, nvecs, matrix_size):
	pass
