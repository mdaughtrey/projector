#!/usr/bin/env python3

import  cv2
import  logging
from    logging.handlers import RotatingFileHandler
import pdb

serdevname='/dev/ttyACM0'
cap = cv2.VideoCapture('/dev/video0')
#res = [(640,480),(3264,2448),(2592,1944),(1920,1080),(1600,1200),(1280,720),(960,540),(848,480),(640,360),(424,240),(320,240),(320,180),(640,480)]

def serwaitfor(text1, text2):
    accum = b''
    logger = logging.getLogger('hqcap')
    logger.debug("Waiting on %s or %s" % (text1, text2))
    while not text1 in accum and not text2 in accum:
        try:
            accum += serdev.read()
        except:
            logger.debug("serwaitfor timeout")
        #logger.debug("Accumulating %s" % accum)
    if text1 in accum:
        logger.debug("Matched on %s" % text1)
        return (0, text1, accum)
    if text2 in accum:
        logger.debug("Matched on %s" % text2)
        return (1, text2, accum)

def init():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    serdev = serial.Serial(serdevname, 115200) # , timeout=1)
    if serdev.isOpen():
        serdev.close()
    serdev.open()
    serwrite(b' ')
    wait = serwaitfor(b'{State:Ready}', b'No')



def genframes():


props = [(a,cap.get(getattr(cv2, a))) for a in dir(cv2) if a.startswith('CAP_PROP')]
for k,v in props:
    if -1.0 == v: continue
    print(f'{k}: {v}')


# CAP_PROP_AUTOFOCUS: 1.0
# CAP_PROP_AUTO_EXPOSURE: 3.0
# CAP_PROP_AUTO_WB: 1.0
# CAP_PROP_BACKEND: 200.0
# CAP_PROP_BACKLIGHT: 0.0
# CAP_PROP_BRIGHTNESS: 20.0
# CAP_PROP_BUFFERSIZE: 4.0
# CAP_PROP_CONTRAST: 50.0
# CAP_PROP_CONVERT_RGB: 1.0
# CAP_PROP_EXPOSURE: 156.0
# CAP_PROP_FORMAT: 16.0
# CAP_PROP_FOURCC: 1448695129.0
# CAP_PROP_FPS: 30.0
# CAP_PROP_FRAME_HEIGHT: 480.0
# CAP_PROP_FRAME_WIDTH: 640.0
# CAP_PROP_GAIN: 57.0
# CAP_PROP_GAMMA: 300.0
# CAP_PROP_HUE: 0.0
# CAP_PROP_MODE: 0.0
# CAP_PROP_POS_MSEC: 0.0
# CAP_PROP_SATURATION: 68.0
# CAP_PROP_SHARPNESS: 50.0
# CAP_PROP_TEMPERATURE: 4600.0
# CAP_PROP_WB_TEMPERATURE: 4600.0


