import pyrtl
from pyrtl import *
from pyrtl import rtllib
from pyrtl.rtllib import multipliers
from pyrtl.rtllib import adders
from pyrtl.rtllib import libutils


def bit_compare(in0, in1):
	'''
	Will return max bit for now
	'''
	out = pyrtl.WireVector(32)
	out_reg = pyrtl.Register(32)
	with pyrtl.conditional_assignment:
		with in0 >= in1:
			out |= in0
		with in0 < in1:
			out |= in1
	out_reg.next <<= out
	return out_reg

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

def intermediate_pool(act_out, matrix_size, pool_size, waddr):
	line_in = []
	for i in act_out: # unsure if we can iterate through act_out b/c it's a wire
		line_in.append(i)
	int_mem = MemBlock(bitwidth=32, addrwidth=16) # addrwidth needs to be log2 of matrix_size
	for x in range(0, matrix_size / pool_size):
		pool_in = []
		# base_index = x * pool_size
		for offset in range(0, pool_size):
			pool_in.append(line_in[(x * pool_size) + offset])
		int_mem[waddr + x] = line_pool(pool_in)
	return int_mem #returns a MemBlock to be appended to int_mem_array

def final_pool(matrix_size, pool_size, raddr, waddr, int_mem_array):
	final_mem = MemBlock(bitwidth=32, addrwidth=16) # addrwidth needs to be log2 of matrix size
	for x in range(0, matrix_size / pool_size):
		pool_in = []
		for i in range(0, matrix_size):
			pool_in.append(int_mem_array[i][raddr + x])
		final_mem[waddr + x] = line_pool(pool_in)
	return final_mem #returns a Memblock to be appended into final_mem_array

def full_pool(act_out, matrix_size, pool_size, raddr, waddr):
	int_mem_array = []
	for depth in range(0, matrix_size): #needs to be done in hardware. counter + clock
		int_mem_array.append(intermediate_pool(act_out, matrix_size, pool_size, waddr))

	final_mem_array = []
	for depth in range(0, matrix_size/pool_size):
		final_mem_array.append(final_pool(matrix_size, pool_size, raddr, waddr, int_mem_array))
	return final_mem_array
	# WE NEED A DONE SIGNAL!!!!!!!!!!!!!!!!!!!!!!!!!!

def pool_top(act_out, matrix_size, pool_size, done, raddr, final_mem_array, nrml_en, pool_en, dest_addr):
	ub_addr = pyrtl.Register(len(dest_addr))
	counter = pyrtl.Register(matrix_size)
	output_wire = pyrtl.WireVector(1)
	output_reg = pyrtl.Register(1)
	output_list = []
	with pyrtl.conditional_assignment:
		with nrml_en:
			result_array |= normalize()
			output_reg.next |= 1
		with pool_en:
			result_array |= full_pool(act_out, matrix_size, pool_size, raddr, waddr)
			output_reg.next |= 1
		with output_reg:
			for mem in result_array:
				output_list.append(mem[raddr])
			output_wire |= concat_list(output_list)
			ub_addr.next |= ub_addr + 1
			counter.next |= counter + 1
			with counter == matrix_size:
				done |= 1
	ub_en = output_reg
	return output_wire

'''
Returns amt to shift values by for normalization
'''
def find_shift_amt(start, max_val):
	busy = Register(1)
	counter = pyrt.Register(5) # count max to 32
	max_val_copy = pyrt.Register(32) # 32bit

	with pyrtl.conditional_assignment:
		with start:
			busy.next |= 1
			counter.next |= 1
			max_val_copy.next |= max_val
			done.next |= 0
		with busy:
			max_val_copy.next |= shift_left_logical(max_val_copy, 1)
			counter.next |= counter + 1
			with max_val[0] == 1:
				busy.next |= 0
				done.next |= 1
	return counter, done
	
'''
Naive Normalization
naive linear normalization:
Find max val. Shift all vals until MSB of max val is the 8th bit
ex:
0001 0010 1110 1111 -> 0000 0000 1001 0111

Inputs:
en - enable (for clocking)

Outputs:
returns mem_array of shifted values

1. full_pool to determine largest val
2. determine shift amount
	a. shift left until MSB is a 1, then shift right 24 times
	b. shift all other values right by 24-left_shift_count from part a
3. shift all values by shift ammount
'''
def normalize(nrml_start, addrwidth, act_out, matrix_size, raddr, waddr):
	mem_array = full_pool(act_out, matrix_size, matrix_size, raddr, waddr)
	max_val = mem_array[raddr]
	left_shift_count, done = find_shift_amt(nrml_start, max_val)
	busy = pyrtl.Register(1)
	addr = pyrtl.Register(addrwidth)
	counter = pyrtl.Register(matrix_size)
	with pyrtl.conditional_assignment:
		with nrml_start:
			busy.next |= 1
			addr.next |= waddr
			counter.next |= 0
		with busy:
			addr.next |= addr + 1
			counter.next |= counter + 1
			for mem in mem_array:
				shift_left_logical(mem[addr])
			with counter == matrix_size:
				busy.next |= 0
	return mem_array

'''
FROM OLD FOLDER
'''
def relu_nrml(din, offset=0): 
 	assert len(din) == 32 
	assert offset <= 24
	dout = pyrtl.WireVector(32)
	with pyrtl.conditional_assignment: 
		with din[-1] == 0: 
			dout |= din
		with pyrtl.otherwise:
			dout |= 0 
	return dout[24-offset:32-offset]


# Test: collects only the 8 LSBs (after relu)
relu_in = pyrtl.Register(bitwidth=32, name='din')
relu_in.next <<= 300
offset = 24
dout = relu_nrml(relu_in, offset)
relu_out = pyrtl.Register(bitwidth=8, name='dout')
relu_out.next <<= dout 

# simulate the instantiated design for 15 cycles
sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)
for cyle in range(35):
	sim.step({})
sim_trace.render_trace()  

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

dout = maxComplex(din)
cmpr_out = pyrtl.Register(bitwidth=32, name='cmpr_out')
cmpr_out.next <<= dout 


# Simulate the instantiated design
sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)
for cycle in range(20):
	sim.step({})
sim_trace.render_trace()