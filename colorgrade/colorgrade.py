#!/bin/env python3

import cv2 as cv
import numpy as np
import pdb


def main():
    pdb.set_trace()
    test = cv.imread('test.png').astype(np.float32)
    reference = cv.imread('reference.png').astype(np.float32)

    // Gray world factor
    avg = np.mean(reference, axis=(0,1))
    gwf = np.mean(avg)
    reference
