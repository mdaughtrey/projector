#!/usr/bin/env python3

import cv2
import numpy as np
import pdb
import sys

def readit(filename):
    pdb.set_trace()
    data = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
    low,high = (data.max() - 10, data.max())
    data[data<low] = 0
    data[data>high] = 0
    data[data != 0] = 255
    pass


readit(sys.argv[1])
