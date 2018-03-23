import pyrtl
import random

# def relu(vec):
# 	for i in vec:
# 		with pyrtl.conditional_assignment:
# 			with i[0] == 1:
# 				i.next |= 0
# 			with pyrtl.otherwise:
# 				pass
# 	return vec
def relu(vec):
    # assert offset <= 24
    # d[-1] of 2's complement is the signed bit
    # if 0 -> falsecase (positive)
    # if 1 -> truecase (negative)
    return [pyrtl.select(d[-1], falsecase=d, truecase=pyrtl.Const(0, len(d))) for d in vec]
# Now all we need to do is call "sim.step" to simulate each clock cycle of our
# design.  We just need to pass in some input each cycle which is a dictionary
# mapping inputs (the *names* of the inputs, not the actual Input instances)
# and a value for that signal each cycle.  In this simple example we
# can just specify a random value of 0 or 1 with python's random module.  We
# call step 15 times to simulate 15 cycles.

# for cycle in range(15):
#     sim.step({
#         'a': random.choice([0, 1]),
#         'b': random.choice([0, 1]),
#         'c': random.choice([0, 1])
#         })

reg_vec = [pyrtl.Register(32) for i in range(0, 8)]
inputs = [pyrtl.Input(32, 'input_{}'.format(i)) for i in range(0, 8)]
test_dict = {
		'input_0': 3,
		'input_1': -39 & 0xFFFFFFFF,
		'input_2': 17,
		'input_3': 7,
		'input_4': -42 & 0xFFFFFFFF,
		'input_5': -18 & 0xFFFFFFFF,
		'input_6': 37,
		'input_7': -6 & 0xFFFFFFFF
		}
output_orig = [pyrtl.Output(32, 'out_orig_{}'.format(i)) for i in range(0, 8)]
output_relu = [pyrtl.Output(32, 'out_relu_{}'.format(i)) for i in range(0, 8)]

for index,reg in enumerate(reg_vec):
	# inputs[index] <<= test_dict[index]
	reg.next <<= inputs[index]
	output_orig[index] <<= reg
relu_func_out = relu(reg_vec)
for i, index in enumerate(output_relu):
	index <<= relu_func_out[i]

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

for cycle in range(35):
	sim.step(test_dict)


# Now all we need to do is print the trace results to the screen. Here we use
# "render_trace" with some size information.
print('--- ReLU Simulation ---')
sim_trace.render_trace(symbol_len=5, segment_size=5)

# a_value = sim.inspect(a)
# print("The latest value of a was: " + str(a_value))

# --- Verification of Simulated Design ---------------------------------------

# Now finally, let's check the trace to make sure that sum and carry_out are actually
# the right values when compared to a python's addition operation.  Note that
# all the simulation is done at this point and we are just checking the wave form
# but there is no reason you could not do this at simulation time if you had a
# really long running design.

# for cycle in range(15):
# 	# Note that we are doing all arithmetic on values NOT wirevectors here.
# 	# We can add the inputs together to get a value for the result
# 	add_result = (sim_trace.trace['a'][cycle] +
# 				  sim_trace.trace['b'][cycle] +
# 				  sim_trace.trace['c'][cycle])
# 	# We can select off the bits and compare
# 	python_sum = add_result & 0x1
# 	python_cout = (add_result >> 1) & 0x1

# You made it to the end!
exit(0)
