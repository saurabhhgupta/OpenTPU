import math
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
    #   out |= in0
    # with pyrtl.otherwise:
    #   out |= in1
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

'''
Shift_test works for truncation
'''
def shift_test(start, vecs, vecs_length, shift_amt): 
    reg_list = [Register(32) for i in range(0, vecs_length)]
    reg_list_2 = [Register(32) for i in range(0, vecs_length)]
    setup = Register(1)
    shifting = Register(1)
    done = Register(1)
    shift_num = Register(4)
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
                reg_list_2[index].next |= barrel_shifter_v2(reg_list[index], 0, 0, shift_num)
            shifting.next |= 0
            done.next |= 1
    return reg_list_2, start, setup, shifting, done, counter

'''
Test finding number of bits to shift
'''
def nrml_test(start, vecs, vec_length):
    reg_list = [Register(32) for i in range(0, vecs_length)]
    setup = Register(1)
    offset = Register(1)
    done = Register(1)
    shift_amt = Register(int(math.log(32, 2)+1))
    max_val = Register(32)
    one_bit = Register(1)
    counter = Register(int(math.log(32, 2)+1))

    with conditional_assignment:
        with start: #setups up registers
            setup.next |= 1
            counter.next |= 0
            done.next |= 0
            shift_amt.next |= 0
            one_bit.next |= 1
        with setup: 
            #shift in values from vecs
            with counter < vecs_length:
                for index in range(0, vecs_length):
                    reg_list[index].next |= vecs[index]
                counter.next |= counter + 1
            with otherwise:
                counter.next |= 0
                offset.next |= 1
                setup.next |= 0
                max_val.next |= line_pool(reg_list)
        with offset:
            with max_val[31] == 1:
                shift_amt.next |= 24-counter
                offset.next |= 0
                done.next |= 1
            with otherwise: #technically missing 0 = max case
                counter.next |= counter + 1
                max_val.next |= barrel_shifter_v2(max_val, 0, 1, one_bit)
    return shift_amt, counter, start, setup, offset, max_val, done

# ---------shift_test here ---------
# reg_vec = [pyrtl.Register(32) for i in range(0, 8)]
# inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
# start = pyrtl.Input(1, 'start')
# start_reg = pyrtl.Register(1, 'start_reg')
# nvecs = pyrtl.Register(4, 'nvecs')
# nvecs.next <<= 8
# mat_size = 8
# pool_size = 2
# vecs_length = 8
# shift_amt = 4
# test_dict = {
#         'input_0': 1,
#         'input_1': 2,
#         'input_2': 3,
#         'input_3': 4,
#         'input_4': 32,
#         'input_5': 64,
#         'input_6': 128,
#         'input_7': 256,
#         'start': 1
#         }
# output_orig = [pyrtl.Output(32, 'out_{}'.format(i)) for i in range(0, vecs_length)]
# reg_list, w_start, w_setup, w_shifting , w_done, w_counter = shift_test(start, reg_vec, vecs_length, shift_amt)

# for index,reg in enumerate(reg_vec):
#     reg.next <<= inputs[index]
# for index,reg in enumerate(reg_list):
#     output_orig[index] <<= reg
# start_reg.next <<= start
# probe(w_start, "w_start")
# probe(w_setup, "w_setup")
# probe(w_shifting, "w_shifting")
# probe(w_done, "w_done")
# probe(w_counter, "w_counter")

# sim_trace = pyrtl.SimulationTrace()
# sim = pyrtl.Simulation(tracer=sim_trace)

# for cycle in range(20):
#     sim.step(test_dict)
#     if(cycle > 1):
#         test_dict = {
#             'input_0': 1, #should return 0
#             'input_1': 2, #should return 1
#             'input_2': 3, #should return 1
#             'input_3': 4, #should return 2
#             'input_4': 32, #should return 16
#             'input_5': 64, #should return 32
#             'input_6': 128, #should return 64 
#             'input_7': 256, #should return 128
#             'start': 0  
#             }
# # Now all we need to do is print the trace results to the screen. Here we use
# # "render_trace" with some size information.
# print('--- Shift Register Simulation ---')
# sim_trace.render_trace(symbol_len=5, segment_size=5)

# -------nrml_test here--------
reg_vec = [pyrtl.Register(32) for i in range(0, 8)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
start = pyrtl.Input(1, 'start')
start_reg = pyrtl.Register(1, 'start_reg')
nvecs = pyrtl.Register(4, 'nvecs')
nvecs.next <<= 8
mat_size = 8
pool_size = 2
vecs_length = 8
shift_amt = 3
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
# output_val = Output(int(math.log(vecs_length, 2))+1, 'output_amt')
output_amt, counter, start, setup, offset, max_val, done = nrml_test(start, reg_vec, vecs_length)

for index,reg in enumerate(reg_vec):
    reg.next <<= inputs[index]
# output_val <<= output_amt
start_reg.next <<= start
probe(output_amt, 'shift_amt')
probe(setup, "w_setup")
probe(offset, "w_offset")
probe(done, "w_done")
probe(max_val, 'max_val')
probe(counter, 'counter')


sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(55):
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
print('--- Simple Normalization Simulation ---')
sim_trace.render_trace(symbol_len=5, segment_size=5)