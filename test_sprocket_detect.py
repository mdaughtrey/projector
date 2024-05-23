#!/usr/bin/env python3
#0./opencvcap.py --serialport /dev/ttyACM0 --camindex 0 --film s8 --framesto ~/share/opencvcap0 --startdia 140 --enddia 80 --res draft
# References:
# https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
# https://github.com/raspberrypi/picamera2/tree/main/picamera2

import  argparse
#import cProfile
import cv2
#from Exscript.util.interact import read_login
#from Exscript.protocols import Telnet
from functools import partial
from    glob import glob, iglob
from    itertools import groupby
from io import StringIO
import  logging
from   logging import FileHandler, StreamHandler
import  math
#from matplotlib import pyplot as plt
#from scipy import ndimage
#import  numpy as np
import  os
import  pdb
#from picamera2 import Picamera2, Preview
from picam_utils import *
#from    PIL import Image, ImageDraw, ImageFilter, ImageOps
#from    scipy import ndimage
import  serial
from SprocketUtils import SprocketUtils
import sys
from    Tension import Tension
import  time
import subprocess
import signal

def handler(signum, frame):
    print('Ctrl-C detected, exiting gracefully')
    sys.exit(0)


last_delta = 0
capmode='RGB'
logger = None

def pcl_framecap():
    parser = argparse.ArgumentParser()
#    parser.add_argument('--camindex', dest='camindex', help='Camera Index (/dev/videoX)', default=0)
    parser.add_argument(dest='do')
    parser.add_argument('--debug', dest='debug', action='store_true', help='debug (no crop, show lines)')
    parser.add_argument('--savework', dest='savework', action='store_true', help='show bad working images')
    parser.add_argument('--saveallwork', dest='saveallwork', action='store_true', help='show all working images')
    parser.add_argument('--film', dest='film', choices=['super8','8mm'], help='8mm/super8', required=True)
    parser.add_argument('--frames', dest='frames', type=int, default=-1, help='Number of frames to capture')
    parser.add_argument('--framesto', dest='framesto', required=True, help='Target Directory')
    parser.add_argument('--logfile', dest='logfile', required=True, help='Log file')
    parser.add_argument('--debugpy', dest='debugpy', action='store_true', help='enable debugpy')
    parser.add_argument('--useframes', dest='useframes', help='Use frame dir instead of camera')
    return parser.parse_args()

def framecap(config):
    global logger

    su = SprocketUtils(config, hires=False, saveworkto=config.framesto, logger=logger)
    for frame in sorted(glob(config.useframes)):
        image = cv2.imread(frame, cv2.IMREAD_ANYCOLOR)
        image = cv2.flip(image,1)
        inSprocket = su.findfunc()(image)[0]
        logger.debug(f'{frame} -> {inSprocket}')
        if inSprocket:
            cv2.imwrite(f'{config.framesto}/{os.path.basename(frame)}',image)



def main():
    signal.signal(signal.SIGINT, handler)
    global config
    global logger

    config = pcl_framecap()
    setLogging(name='tsd',logfilename=config.logfile,console_level='DEBUG')
    logstream = StringIO()
    FormatString='%(asctime)s %(levelname)s %(funcName)s %(lineno)s %(message)s'
    logger = logging.getLogger('tsd')
    logger.setLevel(logging.DEBUG)
    memlog = StreamHandler(stream = logstream)
    memlog.setFormatter(logging.Formatter(fmt=FormatString))
    memlog.setLevel(logging.DEBUG)
    logger.addHandler(memlog)

    if config.debugpy:
        import debugpy
        debugpy.listen(5678)
        print('Waiting for debugger attach')
        debugpy.wait_for_client()
        debugpy.breakpoint()

    framecap(config)
    with open(config.logfile,'wb') as logto:
        logto.write(logstream.getvalue().encode())

main()
