import math
import random
import pyrtl
from pyrtl import *

def barrel_shifter_v2(bits_to_shift, bit_in, direction, shift_dist, wrap_around=0):
    """
    Create a barrel shifter that operates on data based on the wire width

    :param bits_to_shift: the input wire
    :param bit_in: the 1-bit wire giving the value to shift in
    :param direction: a one bit WireVector representing shift direction
        (0 = shift down, 1 = shift up)
    :param shift_dist: WireVector representing offset to shift
    :param wrap_around: ****currently not implemented****
    :return: shifted WireVector
    """
    # Implement with logN stages pyrtl.muxing between shifted and un-shifted values

    val = bits_to_shift
    append_val = bit_in
    log_length = int(math.log(len(bits_to_shift)-1, 2))  # note the one offset

    if wrap_around != 0:
        raise NotImplementedError

    # if len(shift_dist) > log_length:
    #     raise pyrtl.PyrtlError('the shift distance wirevector '
    #                            'has bits that are not used in the barrel shifter')

    for i in range(min(len(shift_dist), log_length)):
        shift_amt = pow(2, i)  # stages shift 1,2,4,8,...
        newval = pyrtl.select(direction, truecase=val[:-shift_amt], falsecase=val[shift_amt:])
        newval = pyrtl.select(direction, truecase=pyrtl.concat(newval, append_val),
                              falsecase=pyrtl.concat(append_val, newval))  # Build shifted value
        # pyrtl.mux shifted vs. unshifted by using i-th bit of shift amount signal
        val = pyrtl.select(shift_dist[i], truecase=newval, falsecase=val)
        append_val = pyrtl.concat(append_val, bit_in)

    return val

def mux_padding(start, vecs, vecs_length, nvecs, matrix_size):
	#need to check to make sure values are stored on which end of the list
	#NOTE: ONLY SUPPORTS 2 INPUTS. MAXPOOL AND PASSED IN VALUE. needs second layer of muxes for additional features
	busy = Register(1)
	done = Register(1)
	constant_val = Const(2147483648) #0x80000000
	counter = Register(int(math.log(matrix_size,2))+1)
	mask = Const(int(math.pow(2, matrix_size)-1)) #0xfff..f
	mux_control = Register(matrix_size)
	output_vecs = [Register(32) for i in range(0,matrix_size)]
	with conditional_assignment:
		with start:
			counter.next |= 0
			done.next |= 0	
			busy.next |= 1
			mux_control.next |= barrel_shifter_v2(mask, 0, 1, vecs_length)
		with busy:
			counter.next |= counter + 1
			with counter == matrix_size:
				busy.next |= 0
				done.next |= 1
			with counter >= nvecs-1: #checks to see if all values have been passed in. 
				mux_control.next |= mask
			with otherwise: 
				mux_control.next |= barrel_shifter_v2(mask, 0, 1, vecs_length)
			for i in range(0, matrix_size):
				output_vecs[i].next |= mux(mux_control[i], vecs[i], constant_val)
	return output_vecs, mux_control, counter, busy, done, mask

reg_vec = [pyrtl.Register(32, 'reg_{}'.format(i)) for i in range(0, 8)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
start = pyrtl.Input(1, 'start')	
nvecs = pyrtl.Register(8, 'nvecs')
vecs_length = Const(4)
nvecs.next <<= 6
mat_size = 8
test_dict = {
		'input_0': 4, 
		'input_1': 4, 
		'input_2': 4, 
		'input_3': 4, 
		'input_4': 4, 
		'input_5': 4, 
		'input_6': 4, 
		'input_7': 4,
		'start': 1
		}
# output_val = Output(int(math.log(vecs_length, 2))+1, 'output_amt')
output_vecs, mux_control, counter, busy, done, mask = mux_padding(start, reg_vec, vecs_length, nvecs, mat_size)

for index,reg in enumerate(reg_vec):
	reg.next <<= inputs[index]
# output_val <<= output_amt

for index,reg in enumerate(output_vecs):
	probe(reg, 'output_vecs_{}'.format(index))
probe(mux_control, 'mux_control')
probe(counter, 'counter')
probe(done, 'done')
probe(busy, 'busy')
probe(mask, 'mask')
# probe(vecs_length, 'vecs_length')

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(30):
	sim.step(test_dict)
	if(cycle >= 0):
		test_dict = {
			'input_0': 4, 
			'input_1': 4, 
			'input_2': 4, 
			'input_3': 4, 
			'input_4': 4, 
			'input_5': 4, 
			'input_6': 4, 
			'input_7': 4,
			'start': 0  
			}
# Now all we need to do is print the trace results to the screen. Here we use
# "render_trace" with some size information.
print('--- Simulation ---')
sim_trace.render_trace(symbol_len=12, segment_size=5)