import cv2
try:
    from libcamera import Transform
except:
    print("No libcamera library found")
import logging
from logging import FileHandler, StreamHandler
from matplotlib import pyplot as plt
import numpy as np
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

def waitSprocket(logger, picam, film:str, desired:bool, savework:bool=False, saveallwork:bool=False) -> None:
#    global picam
    global count
    start = time.time()
    while (time.time() - start) < 5.0:
        buffer = picam.capture_array("lores")
        count += 1
        logger.debug(str(picam.capture_metadata()))
        if 'super8' == film:
            inSprocket = findSprocketS8(logger, buffer, savework=savework, saveallwork=saveallwork)[0]
        else:
            inSprocket = findSprocket8mm(logger, buffer, savework=savework, saveallwork=saveallwork)[0]
        logger.debug(f'inSprocket {inSprocket}, need {str(desired)}')
        if desired == inSprocket:
            return
    raise RuntimeError('timeout')

def inccount():
    global count
    count += 1

def dumpSaved(saved):
    for kk,vv in saved.items():
        cv2.imwrite(f'/tmp/{count}_{kk}.png', vv)

def findSprocket8mm(logger, image, hires=False, savework=False,saveallwork=False):
    logger.debug(f'frame {count}')
    origy,origx = image.shape[:2]
    if saveallwork:
        savework = True
    savedwork = {}
    if savework:
        savedwork['input'] = image.copy()

    if hires:
        xOffset = 350
        image = image[0:500, xOffset:550]
    else:
        xOffset = 97
        image = image[0:170, xOffset:160]

    if savework:
        savedwork['sliced'] = image.copy()
#        cv2.imwrite(f'/tmp/{count}_sliced.png', image)

    #image=np.asarray(cv2.cvtColor(cv2.imread('/media/frames/20240427_1/findsprocket/13_sliced.png'),cv2.COLOR_BGR2GRAY),dtype=np.uint8)

    image2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image3 = np.asarray(image2, dtype=np.uint8)
    image3 = ndimage.grey_erosion(image3, size=(5,5))
    if savework:
        savedwork['eroded'] = image3.copy()
#        cv2.imwrite(f'/tmp/{count}_eroded.png', image3)

    logger.debug(str(image3[80]))
#    low,high = (image3.max() - 10, image3.max())
    low, high = (250,255)

    logger.debug(f'low {low} high {high}')
    image3[image3<low] = 0
    image3[image3>high] = 0
    image3[image3 != 0] = 255
    if savework: 
        savedwork['threshold'] = image3.copy()
#        cv2.imwrite(f'/tmp/{count}_threshold.png', image3)

    def whtest_lores(rect):
#        (_,_,w,h) = cv2.boundingRect(contour)
        return (120 < rect['h'] < 140)
        #return (110 < w < 130) & (100 < h < 120)

    def whtest_hires(rect):
#        (_,_,w,h) = cv2.boundingRect(contour)
        return (303 < rect['h'] < 340)
        #return (437 < w < 457) & (313 < h < 333)

    logger.debug('Image Average {}'.format(np.average(image3)))

    # Find the contours in the thresholded image
    contours, _ = cv2.findContours(image3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in contours:
        x, y, width, height = cv2.boundingRect(c)
        rects.append({'x':x, 'y':y, 'w':width, 'h':height})
        logger.debug(f'x {x} y {y} width {width} height {height}')

    if hires:
        frects = list(filter(whtest_hires, rects))
    else:
        frects = list(filter(whtest_lores, rects))
    logger.debug(f'Found {len(frects)} filtered rects')
    if 1 != len(frects):
        if hires:
            # None of the contours pass the size filter, likely because light
            # leaking around the sprocket when the film was recorded is
            # throwing off the size detection. See if we can synthesize something.
            logger.info(f'Synthesizing rects for frame {count}')
            ones = np.full_like(image3[0], 255)
            # Start in the middle and move up and down
            boundary = 125
            for smin in range(boundary,-1,-1):
                if not all(image3[smin] == ones):
                    break
            logger.debug(f'Upper bound is row {smin}')
            for smax in range(1+boundary,image3.shape[0]):
                if not all(image3[smax] == ones):
                    break
            logger.debug(f'Upper bound is row {smax}')

            frects = [{'x':0, 'y':smin, 'w':200, 'h':smax-smin}]

        if 1 != len(frects):
            dumpSaved(savedwork)
            return (False, 0, 0, 0, 0)
        else:
            return (False, 0, 0, 0, 0)

#    for c in contours:
#        logger.debug('Post filter Area: ' + str(cv2.contourArea(c)))
#        x, y, width, height = cv2.boundingRect(c)
#        logger.debug(f'x {x} y {y} width {width} height {height}')
#    contour = contours[0]
    x,y,w,h = [frects[0][kk] for kk in ['x','y','w','h']]

    # Get the bounding box of the largest contour
#    cx, cy, cw, ch = cv2.boundingRect(contour)
#    if hires:
#        cy += int(origy/4)
#    else:
#        cy += int(origy/3) + xOffset
#
    if savework:
        rectangle = image3.copy()
        cv2.rectangle(rectangle, (x,y),(x+w,y+h), (100,100,100),3)
        savedwork['rectangle'] = rectangle
#        cv2.imwrite(f'/tmp/{count}_rectangle.png', image3)
#        cv2.drawContours(image3, [contour], -1, (100,100,100), thickness=cv2.FILLED)
    x += xOffset

    # Print the size and location of the white square
    logger.debug(f'White square size: {w}x{h} pixels')
    logger.debug(f'White square location: ({x}, {y})')

    if savework:
        savedwork['identified'] = image3.copy()
#        cv2.imwrite(f'/tmp/{count}_identified.png', image3)
    if saveallwork:
        dumpSaved(savedwork)

    return (True, x, y, w, h)

def findSprocketS8(logger, image, hires=False, savework=False, saveallwork=False):
    logger.debug(count)
    origy,origx = image.shape[:2]

    if hires:
        image = image[int(origy/4):origy-int(origy/4),0:int(origx/5)]
    else:
        image = image[int(origy/3):origy-int(origy/3),0:int(origx/5)]

    savedwork = {}
    if savework:
        savedwork['sliced'] = image.copy()
#        cv2.imwrite(f'/tmp/{count}_sliced.png', image)
    image2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image3 = np.asarray(image2, dtype=np.uint8)
    image3 = ndimage.grey_erosion(image3, size=(5,5))
    if savework:
        savedwork['eroded'] = image3.copy()
#        cv2.imwrite(f'/tmp/{count}_eroded.png', image3)

    logger.debug(str(image3[80]))
    low,high = (int(image3.max() * 0.9), image3.max())
    image3[image3<low] = 0
    image3[image3>high] = 0
    image3[image3 != 0] = 255
    if savework: 
        savedwork['threshold'] = image3.copy()
#        cv2.imwrite(f'/tmp/{count}_threshold.png', image3)

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
        savedwork['identified'] = image3.copy()

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
