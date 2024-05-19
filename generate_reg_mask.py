#!/usr/bin/env python3

import logging
from logging import FileHandler, StreamHandler
from picam_utils import *
from SprocketUtils import SprocketUtils

def save(image):
    cv2.imwrite('/tmp/saved.png',image)

def genmask(image):
    xOffset = 97
    image = image[:, xOffset:160]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = np.asarray(image, dtype=np.uint8)
    image = ndimage.grey_erosion(image, size=(5,5))
    low, high = (245,255)

    image[image<low] = 0
    image[image>high] = 0
    image[image != 0] = 255
    save(image)





genmask(cv2.imread('/tmp/44_input.png',cv2.IMREAD_ANYCOLOR))

