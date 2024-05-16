#!/usr/bin/env python3
# coding: utf-8

import  argparse
import cv2
from    glob import glob, iglob
import  logging
from   logging import FileHandler, StreamHandler
import numpy as np
import os
from picam_utils import *
from PIL import Image,ImageDraw,ImageFilter,ImageOps
from    scipy import ndimage
from SprocketUtils import SprocketUtils
import sys

args = None
logger = None

def procargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--readfrom', dest='readfrom', help='read from glob')
    parser.add_argument('--writeto', dest='writeto', help='write to directory', required=True)
    parser.add_argument('--webdb', dest='webdb', help='enable web debugger (port 5555)', action='store_true', default=False)
    parser.add_argument('--film', dest='film', choices=['super8','8mm'], help='8mm/super8', required=True)
    parser.add_argument('--savework', dest='savework', action='store_true', help='show bad working images')
    parser.add_argument('--saveallwork', dest='saveallwork', action='store_true', help='show all working images')
    return parser.parse_args()


def main():
    global args
    global logger
    args = procargs()
    logger = setLogging('registration', '00_registration.log', logging.INFO)['logger']
    if args.readfrom and not os.path.exists(os.path.dirname(args.readfrom)):
        logger.error(f'{args.readfrom} does not exist')
        sys.exit(1)

    realpath = os.path.realpath(args.writeto)
    if not os.path.exists(os.path.dirname(realpath)):
        logger.error(f'{args.writeto} does not exist')
        sys.exit(1)

    su = SprocketUtils(args, hires=True, saveworkto=args.writeto, logger=logger)
    for file in sorted(glob(args.readfrom)):
        writeto = os.path.splitext(os.path.basename(file))[0]
        if os.path.exists(f'{realpath}/{writeto}.reg'):
            su.inccount()
            continue
        (_,x,y,width,height) = su.findfunc()(cv2.imread(file, cv2.IMREAD_ANYCOLOR))
#        if 'super8' == args.film:
#            (_,x,y,width,height) = findSprocketS8(logger, cv2.imread(file, cv2.IMREAD_ANYCOLOR), hires=True, savework=args.savework, saveallwork=args.saveallwork)
#        else:
#            (_,x,y,width,height) = findSprocket8mm(logger, cv2.imread(file, cv2.IMREAD_ANYCOLOR), hires=True, savework=args.savework, saveallwork=args.saveallwork)
        su.inccount()
        with open(f'{realpath}/{writeto}.reg','wb') as out:
            out.write(f'{int(y+height/2)}'.encode())
            #out.write(f'{x+width} {x} {int(y+height/2)}'.encode())

main()
