import cv2
try:
    from libcamera import Transform
except:
    print("No libcamera library found")
import logging
from logging import FileHandler, StreamHandler
from matplotlib import pyplot as plt
import numpy as np
import pdb
try:
    from picamera2 import Picamera2, Preview
except:
    print("No picamera library found")
from scipy import ndimage
import sys
import time

count = 0

class FakeLogger:
    DEBUG = 0
    INFO = 0
    WARNING = 0
    ERROR = 0
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

def init_picam(exposure:int) -> dict:
    camera = {'picam': None}
    lores={"size":(640,480),"format":"RGB888"}
    main={"size":(2304,1296),"format":"RGB888"}

#    global picam
    controls={'FrameDurationLimits':(50000,50000),'ExposureTime': exposure,
              'AeEnable': False, 'AwbEnable': False}
    transform = Transform(hflip=True)
    #Picamera2.set_logging(Picamera2.ERROR)
    Picamera2.set_logging(Picamera2.ERROR)
    camera['picam']= Picamera2()
    cam_config = camera['picam'].create_video_configuration(queue=False,main=main,lores=lores,transform=transform,controls=controls)
    #cam_config = picam.create_video_configuration()

    camera['picam'].configure(cam_config)
    camera['picam'].align_configuration(cam_config)
    camera['picam'].start()
    return camera

def waitSprocket(logger, picam, film:str, desired:bool, savework:bool) -> None:
#    global picam
    global count
    start = time.time()
    while (time.time() - start) < 5.0:
        buffer = picam.capture_array("lores")
        count += 1
        logger.debug(str(picam.capture_metadata()))
        if 'super8' == film:
            inSprocket = findSprocketS8(logger, buffer, savework = savework)[0]
        else:
            inSprocket = findSprocket8mm(logger, buffer, savework = savework)[0]
        logger.debug(f'inSprocket {inSprocket}, need {str(desired)}')
        if desired == inSprocket:
            return
    raise RuntimeError('timeout')

def inccount():
    global count
    count += 1

def findSprocket8mm(logger, image, hires=False, savework=False):
    logger.debug(f'frame {count}')
    if savework:
        cv2.imwrite(f'/tmp/{count}_input.png', image)
    origy,origx = image.shape[:2]

    xOffset = 0

    if hires:
        image = image[0:500, 0:750]
    else:
        image = image[0:170, 0:210]

    if savework:
        cv2.imwrite(f'/tmp/{count}_sliced.png', image)

    #image=np.asarray(cv2.cvtColor(cv2.imread('/media/frames/20240427_1/findsprocket/13_sliced.png'),cv2.COLOR_BGR2GRAY),dtype=np.uint8)

    image2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image3 = np.asarray(image2, dtype=np.uint8)
    image3 = ndimage.grey_erosion(image3, size=(5,5))
    if savework:
        cv2.imwrite(f'/tmp/{count}_eroded.png', image3)

    logger.debug(str(image3[80]))
    low,high = (int(image3.max() * 0.8), image3.max())
#    low, high = (130,170)

    logger.debug(f'low {low} high {high}')
    image3[image3<low] = 0
    image3[image3>high] = 0
    image3[image3 != 0] = 255
    if savework: 
        cv2.imwrite(f'/tmp/{count}_threshold.png', image3)

    def whtest_lores(contour):
        (_,_,w,h) = cv2.boundingRect(contour)
        return (110 < w < 130) & (100 < h < 120)

    def whtest_hires(contour):
        (_,_,w,h) = cv2.boundingRect(contour)
        return (485 < w < 505) & (339 < h < 359)


    # Find the contours in the thresholded image
    contours, _ = cv2.findContours(image3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        logger.debug('Pre filter Area: ' + str(cv2.contourArea(c)))
        x, y, width, height = cv2.boundingRect(c)
        logger.debug(f'x {x} y {y} width {width} height {height}')


    if hires:
        contours = list(filter(whtest_hires, contours))
    else:
        contours = list(filter(whtest_lores, contours))
    logger.debug(f'Found {len(contours)} contours')
    if 1 != len(contours):
        return (False, 0, 0, 0, 0)

    for c in contours:
        logger.debug('Post filter Area: ' + str(cv2.contourArea(c)))
        x, y, width, height = cv2.boundingRect(c)
        logger.debug(f'x {x} y {y} width {width} height {height}')
    contour = contours[0]

    # Get the bounding box of the largest contour
    cx, cy, cw, ch = cv2.boundingRect(contour)
#    if hires:
#        cy += int(origy/4)
#    else:
#        cy += int(origy/3) + xOffset
#
    if savework:
        cv2.rectangle(image3, (cx,cy),(cx+cw,cy+ch), (100,100,100),3)
        cv2.imwrite(f'/tmp/{count}_rectangle.png', image3)
#        cv2.drawContours(image3, [contour], -1, (100,100,100), thickness=cv2.FILLED)

    # Print the size and location of the white square
    logger.debug(f'White square size: {cw}x{ch} pixels')
    logger.debug(f'White square location: ({cx}, {cy})')

    if savework:
        cv2.imwrite(f'/tmp/{count}_identified.png', image3)

    return (True, cx, cy, cw, ch)

def findSprocketS8(logger, image, hires=False, savework=False):
    logger.debug(count)
    origy,origx = image.shape[:2]

    if hires:
        image = image[int(origy/4):origy-int(origy/4),0:int(origx/5)]
    else:
        image = image[int(origy/3):origy-int(origy/3),0:int(origx/5)]

    if savework:
        cv2.imwrite(f'/tmp/{count}_sliced.png', image)
    image2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image3 = np.asarray(image2, dtype=np.uint8)
    image3 = ndimage.grey_erosion(image3, size=(5,5))
    if savework:
        cv2.imwrite(f'/tmp/{count}_eroded.png', image3)

    logger.debug(str(image3[80]))
    low,high = (int(image3.max() * 0.9), image3.max())
    image3[image3<low] = 0
    image3[image3>high] = 0
    image3[image3 != 0] = 255
    if savework: 
        cv2.imwrite(f'/tmp/{count}_threshold.png', image3)

    def whtest_lores(contour):
        (_,_,w,h) = cv2.boundingRect(contour)
        return (40 < w < 60) & (60 < h < 90)

    def whtest_hires(contour):
        (_,_,w,h) = cv2.boundingRect(contour)
        return (144 < w < 216) & (162 < h < 243)

    # Find the contours in the thresholded image
    contours, _ = cv2.findContours(image3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        logger.debug('Pre filter Area: ' + str(cv2.contourArea(c)))
        x, y, width, height = cv2.boundingRect(c)
        logger.debug(f'x {x} y {y} width {width} height {height}')
    if hires:
        contours = list(filter(whtest_hires, contours))
    else:
        contours = list(filter(whtest_lores, contours))
    logger.debug(f'Found {len(contours)} contours')
    if 1 != len(contours):
        return (False, 0, 0, 0, 0)

    for c in contours:
        logger.debug('Post filter Area: ' + str(cv2.contourArea(c)))
        x, y, width, height = cv2.boundingRect(c)
        logger.debug(f'x {x} y {y} width {width} height {height}')
    contour = contours[0]

    # Get the bounding box of the largest contour
    cx, cy, cw, ch = cv2.boundingRect(contour)
    if hires:
        cy += int(origy/4)
    else:
        cy += int(origy/3)

    # Print the size and location of the white square
    logger.debug(f'White square size: {cw}x{ch} pixels')
    logger.debug(f'White square location: ({cx}, {cy})')

    if savework:
        cv2.imwrite(f'/tmp/{count}_identified.png', image3)

    return (True, cx, cy, cw, ch)

def setLogging(name:str,logfilename:str,console_level) -> dict:
    logger = {'logger': None}
    FormatString='%(asctime)s %(levelname)s %(funcName)s %(lineno)s %(message)s'
#    logging.basicConfig(level = logging.DEBUG, format=FormatString)
    
    logger['logger'] = logging.getLogger(name)
    logger['logger'].setLevel(logging.DEBUG)
    fileHandler = FileHandler(filename = logfilename)
    fileHandler.setFormatter(logging.Formatter(fmt=FormatString))
    fileHandler.setLevel(logging.DEBUG)
    logger['logger'].addHandler(fileHandler)

    stdioHandler = StreamHandler(sys.stdout)
    stdioHandler.setFormatter(logging.Formatter(fmt=FormatString))
    stdioHandler.setLevel(console_level)
    logger['logger'].addHandler(stdioHandler)
    return logger
