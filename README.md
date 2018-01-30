# OpenTPU
### Created by Saurabh Gupta & Brandon Pon

OpenTPU is an open-source re-implementation of Google's Tensor Processing Unit (TPU) by the UC Santa Barbara ArchLab. This specific repository includes an add-on of convolution and max pooling.

The TPU is Google's custom ASIC for accelerating the inference phase of neural network computations.

The design is based on details from Google's paper titled "In-Datacentre Performance Analysis of a Tensor Processing Unit" (https://arxiv.org/abs/1704.04760), which is to appear at ISCA2017. However, no formal spec, interface, or ISA has yet been published for the TPU.

#### The OpenTPU is powered by PyRTL (http://ucsbarchlab.github.io/PyRTL/).

## Requirements

- Python 3
- PyRTL version >= 0.8.5
- numpy

Both PyRTL and numpy can be installed with pip; e.g., `pip install pyrtl`.

## How to Run

To run the simple matrix multiply test in both the hardware and functional simulators:

Make sure MATSIZE is set to 8 in config.py, then

```
python3 assembler.py simplemult.a
python3 runtpu.py simplemult.out simplemult_hostmem.npy simplemult_weights.npy
python3 sim.py simplemult.out simplemult_hostmem.npy simplemult_weights.npy
```

To run the Boston housing data regression test in both the hardware and functional simulators:

Make sure MATSIZE is set to 16 in config.py, then
```
python3 assembler.py boston.a
python3 runtpu.py boston.out boston_inputs.npy boston_weights.npy
python3 sim.py boston.out boston_inputs.npy boston_weights.npy
```


### Hardware Simulation
The executable hardware spec can be run using PyRTL's simulation features by running `runtpu.py`. The simulation expects as inputs a binary program and numpy array files containing the initial host memory and the weights.

Be aware that the size of the hardware Matrix Multiply unit is parametrizable --- double check `config.py` to make sure MATSIZE is what you expect.

### Functional Simulation
sim.py implements the functional simulator of OpenTPU. It reads in three cmd args: the assembly program, the host memory file, and the weights file. Due to the different quantization mechnisms between high-level applications (written in tensorflow) and OpenTPU, the simulator runs in two modes: 32b float mode and 8b int mode. The downsampling/quantization mechanism is consistent with the HW implementation of OpenTPU. It generates two sets of outputs, one set being 32b-float typed, the other 8b-int typed.

Example usage:

    python sim.py boston.out boston_input.npy boston_weights.npy

Numpy matrices (.npy files) can be generated by calling `numpy.save` on a numpy array.

checker.py implementes a simple checking function to verify the results from HW, simulator and applications. It checkes the 32b-float application results against 32b-float simulator results and then checks the 8b-int simulator results against 8b-int HW results.

Example usage:

    python checker.py


## FAQs:

### How big/efficient/fast is OpenTPU?
As of the alpha release, we do not have hard synthesis figures for the full 256x256 OpenTPU.

### What can OpenTPU do?
The hardware prototype can currently handle matrix multiplies and activations for ReLU and sigmoid --- i.e., the inference phase of many neural network computations.

### What features are missing?
Convolution, pooling, programmable normalization.

### Does your design follow that of the TPU?
We used high-level design details from the TPU paper to guide our design when possible. Thus, the major components of the chip are the same --- matrix multiply unit, unified buffer, activation unit, accumulator, weight FIFO, etc. Beyond that, the implementations may have many differences.

### Does OpenTPU support all the same instructions as TPU?
No. Currently, OpenTPU supports the RHM, WHM, RW, MMC, ACT, NOP, and HLT instructions (see ISA section for details). The purpose, definition, and specification of other TPU instructions is absent from the published paper. Some instructions will likely be added to OpenTPU as we continue development (such as SYNC), but the final ISA will likely feature many differences without a published spec from Google to work off of.

### Is OpenTPU binary compatible with the TPU?
No. There is no publicly available interface or spec for TPU.

### I'd like to do some analysis/extensions of OpenTPU, but I need Verilog. Do you have a Verilog version?
PyRTL can can output structural Verilog for the design, using the `OutputToVerilog` function.


## Software details

### ISA

- RHM src, dst, N
Read Host Memory.
Read _N_ vectors from host memory beginning at address _src_ and save them in the UB (unified buffer) beginning at address _dst_.
- WHM src, dst, N
Write Host Memory.
Write _N_ vectors from the UB beginning at address _src_ to host memory beginning at address _dst_.
- RW addr
Read Weights.
Load the weights tile from the weights DRAM at address _addr_ into the on-chip FIFO.
- MMC.{OS} src, dst, N
Matrix Multiply/Convolution.
Perform a matrix multiply operation on the _N_ vectors beginning at UB address _src_, storing the result in the accumulator buffers beginning at address _dst_. If the _O_ (overwrite) flag is specified, overwrite the contents of the accumulator buffers at the destination addresses; default behavior is to add to the value there and store the new sum. If the _S_ (switch) flag is specified, switch to using the next tile of weights, which must have already been pre-loaded. The first `MMC` instruction in a program should always use the _S_ flag.
- ACT.{RQ} src, dst, N
Activate.
Perform activation on _N_ vectors in the accumulator buffers starting at address _src_, storing the results in the UB beginning at address _dst_. Activation function is specified with a flag: _R_ for ReLU and _Q_ for sigmoid. With no flag, values are passed through without activation. Normalization is programmable at synthesis-time, but not at run-time; by default, after activation the upper 24 bits are dropped from each value, producing an 8-bit integer.
- NOP
No op. Do nothing for one cycle.
- HLT
Halt. Stop simulation.


### Writing a Program
OpenTPU uses no dynamic scheduling; all execution is fully determinstic* and the hardware relies on the compiler to correctly schedule operations and pad NOPs to handle delays. This OpenTPU release does \
not support "repeat" flags on instructions, so many NOPs are required to ensure correct execution.

*DRAM is a source of non-deterministic latency, discussed in the Memory Controller section of Microarchitecture.

### Generating Data
__Application__

1. Simple one hot 2-layer NN

gen_one_hot.py generates 8b-int typed random squre matrix as training data and vector as label, example usage:
    
    python gen_one_hot.py --path simple_train --shape 8 8 --range -5 5
    python gen_one_hot.py --path simple_train_label --shape 8 1 --range 0 2

simple_nn.py trains a simple 2-layer nn on the given train/label dataset and writes the weights into a file, example usage (run gen_one_hot example first to generate the files):
    
    python simple_nn.py --path simple_train.npy --label simple_train_label.npy

After running the above command, two files are generated: simple_nn_weight_dram.npy is the 8b-int typed weight dram that the OpenTPU operates on, simple_nn_gt is the pickled ground truth 32b-float resulits and weights. To run with OpenTPU, a test file must also be generated, example usage:

    python gen_one_hot.py --path simple_test --shape 100 8 --range 1, 9

After which simple_test.npy will be generated and it should be used as the host memory by OpenTPU.

We also provide simple_nn.a -- the assembly program for this simple nn.

2. Tensorflow DNN regression

Although applications written in any high-level nn framework can be used, here we use tensorflow as an example.

tf_nn.py trains a MLP regressor on the Boston Housing Dataset (https://archive.ics.uci.edu/ml/datasets/housing). Example usage:
    
    python tf_nn.py --N 10 --save-input-path boston_input --save-weight-path boston_weights --save-output-path boston_output
    python tf_nn.py --N 10 --save-input-path boston_input --save-weight-path boston_weights --save-output-path boston_output --raw

After running the above command, four files are generated: gt32.npy holds the ground truth prediction values, boston_input.npy holds the input test cases which is used as the host memeory for OpenTPU, boston_output.npy holds all the intermediate output values, and boston_weights.npy holds the weight matrices which are used as the weight dram for OpenTPU.

Adding --raw to the command generates 32b-float typed files instead of 8b ints.


### Latencies
The following gives the hardware execution latency for each instruction on OpenTPU:

- RHM - _M_ cycles for reading _M_ vectors
- WHM - _M_ cycles for writing _M_ vectors
- RW - _N*N_/64 cycles for _N_x_N_ MM Array for DRAM transfer, and up to 3 additional cycles to propagate through the FIFO
- MMC - _L+2N_ cycles, for _N_x_N_ MM Array and _L_ vectors multiplied in the instruction
- ACT - _L+1_ cycles, for _L_ vectors activated in the instruction


## Microarchitecture

### Matrix Multiply (MM) Unit
The core of the compute of the OpenTPU is the parametrizable array of 8-bit Multiply-Accumulate Units (MACs), each consisting of an 8-bit integer multiplier and an integer adder of between 16 and 32 bits\
*. Each MAC has two buffers storing 8-bit weights (the second buffer allows weight programming to happen in parallel). Input vectors enter the array from the left, with values advancing one unit to the r\
ight each cycle. Each unit multiplies the input value by the active weight, adds it to the value from the unit above, and passes the result to the unit below. Input vectors are fed diagonally so that val\
ues align correctly as partial sums flow down the array.

*The multipliers produce 16-bit outputs; as values move down the columns of the array, each add produces 1 extra bit. Width is capped at 32, creating the potential for uncaught overflow.


### Accumulator Buffers
Result vectors from the MM Array are written to a software-specified address in a set of accumulator buffers. Instructions indicate whether values should be added into the value already at the address or\
 overwrite it. MM instructions read from the Unified Buffer (UB) and write to the accumulator buffers; activate instructions read from the accumulator buffers and write to the UB.


### Weight FIFO
At scale (256x256 MACs), a full matrix of weights (a "tile") is 64KB; to avoid stalls while weights are moved from off-chip weight DRAM, a 4-entry FIFO is used to buffer tiles. It is assumed the connecti\
on to the weight DRAM is a standard DDR interface moving data in 64-byte chunks (memory controllers are currently emulated with no simulated delay, so one chunk arrives each cycle). When an MM instructio\
n carries the "switch" flag, each MAC switches the active weight buffer as first vector of the instruction propagates through the array. Once it reaches the end of the first row, the FIFO begins feeding \
new weight values into the free buffers of the array. New weight values are passed down through the array each cycle until each row reaches its destination.


### Systolic Setup
Vectors are read all at once from the Unified Buffer, but must be fed diagonally into the MM Array. This is accomplished with a set of sequential buffers in a lower triangular configuration. The top valu\
e reaches the matrix immediately, the second after one cycle, the third after two, etc., so that each value reaches a MAC at the same time as the corresponding partial sum from the same source vector.


### Memory Controllers
Currently, memory controllers are emulated and have no delay. The connection to Host Memory is currently the size of one vector. The connection to the Weight DRAM uses a standard width of 64 bytes.

Because the emulated controllers can return a new value each cycle, the OpenTPU hardware simulation currently has no non-detministic delay. With a more accurate DRAM interface that may encounter dynamic \
delays, programs would need to either take care to schedule for the worst-case memory delay, or make use of another instruction to ensure memory operations complete before the values are required*.

*We note that the TPU "SYNC" instruction may fulfill this purpose, but is currently unimplemented on OpenTPU.


### Configuration
Unified Buffer size, Accumulator Buffer size, and the size of the MM Array can all be specified in config.py. However, the MM Array must always be square, and vectors/weights are always composed of 8-bit integers.
 
