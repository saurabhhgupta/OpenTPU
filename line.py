import math
import random
import pyrtl
from pyrtl import *

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
	while i <= len(pool_in) - 2:
		new_array.append(bit_compare(pool_in[i], pool_in[i+1]))
		i += 2
	if len(pool_in) == 2:
		return bit_compare(pool_in[0], pool_in[1])
	return line_pool(new_array)


# Simulation
input_vec = [pyrtl.Register(32, 'reg_{}'.format(i)) for i in range(0, 8)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
test_dict = {
		'input_0': 45,
		'input_1': 4,
		'input_2': 53,
		'input_3': 12,
		'input_4': 28,
		'input_5': 31,
		'input_6': 39,
		'input_7': 88,
		}
output = pyrtl.Output(32, 'output')

for index,reg in enumerate(input_vec):
	reg.next <<= inputs[index]
output <<= line_pool(input_vec)

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(35):
	sim.step(test_dict)

print('--- line_pool() simulation ---')
sim_trace.render_trace(symbol_len=5, segment_size=5)