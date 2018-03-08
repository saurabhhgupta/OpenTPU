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

def pool_top(done, raddr, final_mem_array, select_sig):
	value_array = []
	for i in final_mem_array:
		value_array.append(i[raddr])
		raddr += 1
	return concat_list(value_array)

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