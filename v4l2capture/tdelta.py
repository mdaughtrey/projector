#!/bin/env python3

import time
import numpy as np
import pdb

def main():
    pdb.set_trace()
    data = open('usbcap.log', 'rb').readlines()
    data0 = np.asarray([int(time.mktime(time.strptime(x.decode().split(',')[0], '%Y-%m-%d %H:%M:%S'))) for x in data])
    deltas = np.diff(data0)
    aa = np.argsort(deltas)
    for bb in aa[-10:]:
        print(f'Line {bb} delta {deltas[bb]}')

    pass


main()

#2023-01-26 19:47:40,102 DEBUG init 84 Length 14m, 5439 Frames
