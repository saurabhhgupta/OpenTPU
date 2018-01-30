import argparse
import numpy as np


args = None

def gen_mem(path, fill):
    np.save(path, fill)

def parse_args():
    global args

    parser = argparse.ArgumentParser()

    parser.add_argument('--path', action='store',
                        help='path to source file.')
    parser.add_argument('--shape', action='store', type=int, nargs='+',
                        help = 'shape of matrix to generate.')
    parser.add_argument('--debug', action='store_true',
                        help='switch debug prints.')
    args = parser.parse_args()


if __name__ == '__main__':
    parse_args()
    mem = np.random.rand(*args.shape)
    gen_mem(args.path, mem)
