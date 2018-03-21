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

def shift_test(start, vecs, vecs_length, shift_amt):
    reg_list = [Register(32) for i in range(0, vecs_length)]
    setup = Register(1)
    shifting = Register(1)
    done = Register(1)
    shift_num = Register(3)
    counter = Register(int(math.log(vecs_length, 2))+1)

    with conditional_assignment:
        with start:
            setup.next |= 1
            shifting.next |= 0
            counter.next |= 0
            done.next |= 0
            shift_num.next |= shift_amt
        with setup:
            #shift in values from vecs
            with counter < vecs_length:
                for index in range(0, vecs_length):
                    reg_list[index].next |= vecs[index]
                counter.next |= counter + 1
            with otherwise:
                counter.next |= 0
                shifting.next |= 1
                setup.next |= 0
        with shifting:
            for index in range(0, vecs_length):
                reg_list[index].next |= barrel_shifter_v2(reg_list[index], 0, 0, shift_num)
            shifting.next |= 0
            done.next |= 1
    return reg_list, start, setup, shifting, done, counter



reg_vec = [pyrtl.Register(32, 'reg_{}'.format(i)) for i in range(0, 8)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
start = pyrtl.Input(1, 'start')
start_reg = pyrtl.Register(1, 'start_reg')
nvecs = pyrtl.Register(4, 'nvecs')
nvecs.next <<= 8
mat_size = 8
pool_size = 2
vecs_length = 8
shift_amt = 1
test_dict = {
        'input_0': 1,
        'input_1': 2,
        'input_2': 3,
        'input_3': 4,
        'input_4': 32,
        'input_5': 64,
        'input_6': 128,
        'input_7': 256,
        'start': 1
        }
output_orig = [pyrtl.Output(32, 'out_{}'.format(i)) for i in range(0, vecs_length)]
reg_list, w_start, w_setup, w_shifting , w_done, w_counter = shift_test(start, reg_vec, vecs_length, shift_amt)

for index,reg in enumerate(reg_vec):
    reg.next <<= inputs[index]
for index,reg in enumerate(reg_list):
    output_orig[index] <<= reg
start_reg.next <<= start
probe(w_start, "w_start")
probe(w_setup, "w_setup")
probe(w_shifting, "w_shifting")
probe(w_done, "w_done")
probe(w_counter, "w_counter")

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(20):
    sim.step(test_dict)
    if(cycle > 1):
        test_dict = {
            'input_0': 1, #should return 0
            'input_1': 2, #should return 1
            'input_2': 3, #should return 1
            'input_3': 4, #should return 2
            'input_4': 32, #should return 16
            'input_5': 64, #should return 32
            'input_6': 128, #should return 64 
            'input_7': 256, #should return 128
            'start': 0  
            }
# Now all we need to do is print the trace results to the screen. Here we use
# "render_trace" with some size information.
print('--- Simulation ---')
sim_trace.render_trace(symbol_len=5, segment_size=5)