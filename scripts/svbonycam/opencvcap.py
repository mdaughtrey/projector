#!/usr/bin/python3

import argparse
from glob import glob, iglob
import logging
from logging.handlers import RotatingFileHandler
import os
import pdb
import re
import serial
import signal
import subprocess
import sys
import time
import math

from Tension import Tension

import warnings
warnings.filterwarnings('default',category=DeprecationWarning)

SPOOLTYPE="SMALL"
PREFRAMES=1
FRAMES=0
MAXINFLIGHT=30
port = 0
tension = list()
lastTension = 0
numframes = 0

FormatString='%(asctime)s %(levelname)s %(lineno)s %(message)s'
logging.basicConfig(level = logging.DEBUG, format=FormatString)
logger = logging.getLogger('hqcap')
fileHandler = logging.FileHandler(filename = './hqcap.log')
fileHandler.setFormatter(logging.Formatter(fmt=FormatString))
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

parser = argparse.ArgumentParser()
parser.add_argument('--frames', dest='frames', type=int, default=1e6, help='number of frames to capture')
parser.add_argument('--serialport', dest='serialport', default='/dev/ttyACM0', help='serial port device')
parser.add_argument('--camindex', dest='camindex', help='Camera Index (/dev/videoX)', default=0)
parser.add_argument('--prefix', dest='prefix', default='', help='prefix filenames with a prefix')
parser.add_argument('--film', dest='film', choices=['s8','8mm'], help='8mm/s8', default='s8')
parser.add_argument('--framesto', dest='framesto', required=True, help='Target Directory', default='/mnt/exthd')
parser.add_argument('--startdia', dest='startdia', type=int, default=62, help='Feed spool starting diameter (mm)')
parser.add_argument('--enddia', dest='enddia', type=int, default=35, help='Feed spool ending diameter (mm)')
parser.add_argument('--res', dest='res', choices=['draft','1k', 'hd', 'full'], help="resolution", default='draft')
config = parser.parse_args()

#    res = {'draft':(640, 480), '1k':(1024,768), 'hd':(1920, 1080), 'full':(4056, 3040)}


def signal_handler(signal, frame):
    port.write(b' ')
    portWaitFor(port, b'{State:Ready}')
    port.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


#def portWaitFor(port, text):
#    accum = b''
#    logger.debug("Waiting on %s" % text)
#    while not text in accum:
#        accum += port.read()
#        #logger.debug("Accumulating %s" % accum)
#    logger.debug("Received %s" % text)
#    return accum

def portWaitFor(port, text):
    accum = b''
    if isinstance(text, bytes):
        text = [text]

    logger.debug("Waiting on %s" % str(text))

    res = [False]
    
    while True not in res:
        accum += port.read()
#        logger.debug(f'Accumulated {accum}')
        res = [t in accum for t in text]
#        logger.debug(f'res {res}')

    logger.debug(f'portWaitFor {accum}')
    logger.debug(f'portWaitFor {res.index(True)}')
    return text[res.index(True)]


def captureWaitFor2(proc, text1, text2):
    accum = b''
    logger.debug("Waiting on %s or %s" % (text1, text2))
    while not text1 in accum and not text2 in accum:
        try:
#            (out, err) = proc.communicate(timeout=1)
            accum += proc.stderr.read1()
        except:
            logger.debug("captureWaitFor timeout")
        logger.debug("Accumulating %s" % accum)
    if text1 in accum:
        logger.debug("Matched on %s" % text1)
        return (0, text1)
    if text2 in accum:
        logger.debug("Matched on %s" % text2)
        return (1, text2)

def init(framenum):
    global tension
    t = Tension()
    global numframes
    (filmlength, numframes, tension) = t.feedstats(config.startdia, config.enddia)
    numframes += 1000
    logger.debug("Length {}m, {} Frames".format(math.floor(filmlength/1000), numframes))
    map (lambda x: x * 3, tension)

    global lastTension
    lastTension = tension[0]

    logger.debug("Opening %s" % config.serialport)
    serPort = serial.Serial(config.serialport, 115200) # , timeout=1)
    if serPort.isOpen():
        serPort.close()
    serPort.open()
#$    serPort.write(b' ')
#    if b'{State:Ready}' != portWaitFor(serPort, b'{State:Ready}'):
#        logger.debug("Init failed")
#        sys.exit(1)

    serPort.write(str.encode(f'{lastTension}tl1d2D{interval}e0E6000o'))
#    portWaitFor(serPort, b'{State:Ready}')
#    if False == config.noled:
#        serPort.write(b'l')
#    serPort.write(b'c%st' % {'8MM': 'd', 'SUPER8': 'D'}[FILMTYPE]) 
#    serPort.write("vc{}{}T".format({'8mm': 'd', 'super8': 'D'}[config.film], tension[0]).encode('utf-8'))
    #serPort.write("vc{}{}T".format({'8mm': 'd', 'super8': 'D'}[config.film].encode('utf-8'), tension[0]))
#    portWaitFor(serPort, b'{pt:')
    return serPort

def stop(port):
    port.write(b' ')
    portWaitFor(port, b'{State:Ready}')
    logger.debug("Closing")
    port.close()

def frame(port, num):
    global lastTension
    try:
        if (tension[num] != lastTension) & (num < (len(tension) - 1)):
            lastTension = tension[num]
            port.write('-{}t'.format(tension[num]*3).encode('utf-8'))
            logger.debug("Set tension {}".format(lastTension))
    except:
        pass

    if False == config.nofilm:
        port.write(b'?')
        portWaitFor(port, [b'End Config'])

        logger.debug(f'Serial write {msg}')
        if b'{NTO}' == portWaitFor(port, [b'{HDONE}', b'{NTO}']):
            logger.error("Frame init timed out, exiting")
            port.write(b' ')
            sys.exit(0)

#    if config.singleframe:
#        ii = zip([SHUTTER[1]], ['a'])
#    else:
#        ii = zip(SHUTTER, ['a','b','c'])
#
#    logger.debug("40")

    if config.nocam:
        time.sleep(2)
        logger.debug("nocam click")
        return 0

        open("{:s}/{:06d}{:s}.done".format(config.dir, num, tag), "w")
        
    return 0


def main():
    os.makedirs(config.framesto, exist_ok=True);
    files = sorted(glob("{0}/{1}????????.bmp".format(config.dir, config.prefix)))
    if len(files):
        frameNum = int(files[-1][-11:-5]) + 1
    else:
        frameNum = 0
    logger.debug("Starting at frame {0}".format(frameNum))
    global port
    port = init(frameNum)
    frameCount = 0
    #for frameCount in range(0, config.frames):
    for frameCount in range(0, min(config.frames, numframes)):
        while True:
            statvfs = os.statvfs(config.dev)
            if 20e6 < statvfs.f_frsize * statvfs.f_bavail:
                break;
            else:
                logger.info('Waiting for disk space')
                time.sleep(10)
        if frame(port, frameNum): break
        frameNum += 1
    stop(port)
    open("{:s}/{:s}done.done".format(config.dir, config.prefix), "w")

main()

