#!/usr/bin/env python3
# coding: utf-8

import argparse
import cv2
from glob import glob, iglob
import logging
from   logging import FileHandler, StreamHandler
import numpy as np
import os
from picam_utils import *
from PIL import Image,ImageDraw,ImageFilter,ImageOps
import re
import sys

logger = None
args = None

def procargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--readfrom', dest='readfrom', help='read .reg files from directory', required=True)
    parser.add_argument('--writeto', dest='writeto', help='write rotated/cropped images to directory', required=True)
    parser.add_argument('--annotate', dest='annotate', help='annotate frames', action='store_true', default=False)
    parser.add_argument('--markonly', dest='markonly', help='mark frames', action='store_true', default=False)
    parser.add_argument('--exposures', dest='exposures', help='exposures', required=True)
    parser.add_argument('--film', dest='film', choices=['super8','8mm'], help='8mm/super8', required=True)
    return parser.parse_args()

def getRectS8(leftX, centerY):
    boxLeft = int(leftX) + 180
    boxRight = boxLeft + 1250 
    boxTop = int(centerY) - 500
    boxBot = int(centerY) + 500

    return boxLeft,boxRight,boxTop,boxBot

def getRect8mm(centerY):
    return (720,2010,max(centerY-20,0),centerY+980)
#    boxLeft = int(leftX) + 180
#    boxRight = boxLeft + 1520
#    boxTop = int(centerY) - 160
#    boxBot = int(centerY) + 1000
#    return boxLeft,boxRight,boxTop,boxBot

#def cropAndRotate(regfile, imagefile):
def cropAndRotate(centerY, readfrom, writeto):
    try:
        image = cv2.imread(readfrom, cv2.IMREAD_ANYCOLOR)
    except Exception as ee:
        logger.error(f'Error reading from {imagefile}: {str(ee)}')

    if 'super8' == args.film:
        boxLeft,boxRight,boxTop,boxBot = getRectS8(centerY)
    else:
        boxLeft,boxRight,boxTop,boxBot = getRect8mm(centerY)
    height, width = image.shape[:2]
#    rMatrix = cv2.getRotationMatrix2D(center=(width/2,height/2),angle=rotate,scale=1)
#    rImage = cv2.warpAffine(src=image,M=rMatrix,dsize=(width,height))
    logger.debug(writeto)
    logger.debug(f'centerY {centerY} boxLeft {boxLeft} boxRight {boxRight} boxTop {boxTop} boxBot {boxBot}')

    rImage = image
    if args.markonly:
#        cv2.circle(original,(int(avgright),int((avgtop+avgbot)/2)),12,(0,255,0),-1)
        rImage = cv2.rectangle(rImage, (boxTop, boxLeft), (boxBot, boxRight), (0,255,0), 1)
    else:
        rImage = rImage[boxTop:boxBot,boxLeft:boxRight]
    if args.annotate:
        org = (50,350)
        # write the text on the input image
        imageNum = os.path.splitext(os.path.basename(readfrom))[0].split('_')[0]
        cv2.putText(rImage, imageNum, org, fontFace = cv2.FONT_HERSHEY_COMPLEX, fontScale = 1.5, color = (250,225,100))
    logger.debug(f'Writing shape {str(rImage.shape)}')
    cv2.imwrite(writeto, rImage)

def main():
    global args
    global logger
    logger = setLogging('car','01_crop_and_rotate.log',logging.INFO)['logger']
    args = procargs()

#    readpath = os.path.realpath(args.readfrom)
    readpath = args.readfrom
    if not os.path.exists(os.path.dirname(readpath)):
        logger.error(f'{readpath} does not exist')
        sys.exit(1)

#    writepath = os.path.realpath(args.writeto)
    writepath = args.writeto
    if not os.path.exists(writepath):
        logger.info(f'Creating directory {writepath}')
        os.mkdir(writepath)

    exposures = [int(x) for x in args.exposures.split(',')]
    for regfile in sorted(glob(readpath)):
        centerY = int(open(regfile.encode(),'rb').read().strip())
#        if centerX is None:
#            centerX = cX
        for exposure in exposures[1:]:
            filename = os.path.basename(regfile).split('_')
            filename = f'{filename[0]}_{exposure}.png'
            readfrom = os.path.dirname(readpath) + '/' + filename
            writeto = writepath + '/' + filename
            #writeto = realpath + '/' +  os.path.splitext(os.path.basename(regfile))[0] + '.png'
            logger.info(f'{filename}')
            #if not os.path.exists(writeto) | 0 == os.path.getsize(writeto):
            if not os.path.exists(writeto):
                try:
                    cropAndRotate(centerY, readfrom, writeto)
                except Exception as ee:
                    logger.warning(f'Skipping {writeto}: {str(ee)}')

main()
