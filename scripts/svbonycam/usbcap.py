#!/usr/bin/env python3

import argparse
import cv2
import pdb
import time

def proc_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames', dest='frames', type=int, default=-1, help='frames to capture')
    parser.add_argument('--camindex', dest='camindex', help='Camera Index (/dev/videoX)', default=0)
    parser.add_argument('--prefix', dest='prefix', default='', help='prefix filenames with a prefix')
    parser.add_argument('--film', dest='film', choices=['super8','8mm'], help='8mm/super8')
    parser.add_argument('--framesto', dest='framesto', required=True, help='Target Directory')
    parser.add_argument('--startdia', dest='startdia', type=int, default=62, help='Feed spool starting diameter (mm)')
    parser.add_argument('--enddia', dest='enddia', type=int, default=35, help='Feed spool ending diameter (mm)')
    return parser.parse_args()

def framecap(config):
    framecount = 0
    cap = cv2.VideoCapture(config.camindex)
    for x in range(1,10):
        ret, frame = cap.read()
        cv2.imwrite("{}/{:>08}.bmp".format(config.framesto, framecount), frame)
        framecount += 1
        time.sleep(1.0)
    cap.release()



def main():
    config = proc_commandline()
    pdb.set_trace()
    framecap(config)

main()
