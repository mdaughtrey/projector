import cv2
from functools import partial
try:
    from libcamera import Transform
except:
    print("No libcamera library found")
import numpy as np
import os
from scipy import ndimage
try:
    from picamera2 import Picamera2, Preview
except:
    print("No picamera library found")

from glob import glob, iglob
from scipy import ndimage
import time
import tomllib

class MockLogger:
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

class SprocketUtils:
    def __init__(self, config:dict, hires:bool, logger=MockLogger()):
        if not config.film in ['super8','8mm']:
            raise RuntimeError('Invalid film spec (super8/8mm)')
        [setattr(self, name, getattr(config,name,None)) for name in ['project','film','savework','saveallwork']]
        self.logger = logger
        self.hires = hires
        self.savedwork = {}
        self.count = 0
        if self.hires:
            self.__findfunc = partial(SprocketUtils.__findSprocket_contours,self)
        else:
            self.__findfunc = partial(SprocketUtils.__findSprocket_window,self)
        captureconf = self.__proctoml()['capture']
#        captureconf = dict(captureconf.keys(), map(int, captureconf.values))
        self.winX = captureconf['winx'] # int(self.__proctoml()['capture'].get('winx',50))
        self.winY = captureconf['winy'] # int(self.__proctoml()['capture'].get('winx',50))
        self.winW = captureconf['winw'] # int(self.__proctoml()['capture'].get('winw',110))
        self.winH = captureconf['winh'] # int(self.__proctoml()['capture'].get('winw',110))

    def __proctoml(self) -> {}:
        if not os.path.exists(tname := f'{self.project}/config.toml'):
            return {}
        with open(tname,'rb') as tfile:
            return tomllib.load(tfile)


    def __dumpSaved(self) -> None:
        for kk,vv in self.savedwork.items():
            cv2.imwrite(f'{self.project}/work/{self.count}_{kk}.png', vv)
 
    def __findSprocket_window(self,image) -> None:
        self.logger.debug(f'frame {self.count}')
        origy,origx = image.shape[:2]
        if self.saveallwork:
            self.savework = True


        if self.hires:
            xOffset = 350
            image = image[0:500, xOffset:550]
        else:
            # winY,winH = (20,60)
            if self.savework:
                self.savedwork['input'] = image.copy()
                cv2.rectangle(self.savedwork['input'], (self.winX,self.winY),(self.winX+self.winW,self.winY+self.winH), (255,255,255),1)
#            cv2.rectangle(image, (winX+1,winY+1),(winX+winW,winY+winH), (0,0,0),1)
            image = image[self.winY:self.winY+self.winH, self.winX:self.winX+self.winW]

        if self.savework:
            self.savedwork['sliced'] = image.copy()

        image2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image3 = np.asarray(image2, dtype=np.uint8)
#        image3 = ndimage.grey_erosion(image3, size=(5,5))
        if self.savework:
            self.savedwork['eroded'] = image3.copy()

        self.logger.debug(str(image3[int(self.winH/2)]))
        low, high = (235,255)

        self.logger.debug(f'low {low} high {high}')
        image3[image3<low] = 0
        image3[image3>high] = 0
        image3[image3 != 0] = 255 
        if self.savework: 
            self.savedwork['threshold'] = image3.copy()

#        testagainst = np.full_like(image3,255)
        test = np.array_equal(image3,np.full_like(image3,255))
        self.logger.debug(f'test {test}')
        if test:
            return (True,self.winX,self.winY,self.winW,self.winH)
        else:
            return (False,0,0,0,0)


    def __findSprocket_contours(self,image) -> None:
        self.logger.debug(f'frame {self.count}')
        origy,origx = image.shape[:2]
        if self.saveallwork:
            self.savework = True
        if self.savework:
            self.savedwork['input'] = image.copy()

        if self.hires:
            xOffset = 350
            image = image[0:500, xOffset:550]
        else:
            xOffset = 97
            image = image[0:140, xOffset:160]
            #image = image[0:170, xOffset:160]

        if self.savework:
            self.savedwork['sliced'] = image.copy()

        image2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image3 = np.asarray(image2, dtype=np.uint8)
#        image3 = ndimage.grey_erosion(image3, size=(5,5))
        if self.savework:
            self.savedwork['eroded'] = image3.copy()

        self.logger.debug(str(image3[70]))
        low, high = (235,255)

        self.logger.debug(f'low {low} high {high}')
        image3[image3<low] = 0
        image3[image3>high] = 0
        image3[image3 != 0] = 255 
        if self.savework: 
            self.savedwork['threshold'] = image3.copy()

        def whtest_lores(rect:dict):
            return (125 < rect['h'] < 145) and 63 == rect['w']

        def whtest_hires(rect:dict):
            return (230 < rect['h'] < 400)

#        self.logger.debug('Image Average {}'.format(np.average(image3)))

        # Find the contours in the thresholded image
        contours, _ = cv2.findContours(image3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        rects = [dict(zip(('x','y','w','h'),cv2.boundingRect(c))) for c in contours]
        if 0 == len(rects):
            pass
        for r in rects:
            self.logger.debug(str(r))
        _ = map(lambda x: self.logger.debug(str(x)),rects)
#        rects = []
#        for c in contours:
#            x, y, width, height = cv2.boundingRect(c)
#            rects.append({'x':x, 'y':y, 'w':width, 'h':height})
#            self.logger.debug(f'x {x} y {y} width {width} height {height}')

        if self.hires:
            frects = list(filter(whtest_hires, rects))
        else:
            frects = list(filter(whtest_lores, rects))
        self.logger.debug(f'Found {len(frects)} filtered rects')
        if 1 != len(frects):
            if self.hires:
                # None of the contours pass the size filter, likely because light
                # leaking around the sprocket when the film was recorded is
                # throwing off the size detection. See if we can synthesize something.
                self.logger.info(f'Synthesizing rects for frame {self.count}')
                ones = np.full_like(image3[0], 255)
                # Start in the middle and move up and down
                boundary = 125
                for smin in range(boundary,-1,-1):
                    if not all(image3[smin] == ones):
                        break
                self.logger.debug(f'Upper bound is row {smin}')
                for smax in range(1+boundary,image3.shape[0]):
                    if not all(image3[smax] == ones):
                        break
                self.logger.debug(f'Upper bound is row {smax}')

                frects = [{'x':0, 'y':smin, 'w':200, 'h':smax-smin}]

            if self.saveallwork:
                self.__dumpSaved()

        if 1 != len(frects):
            return (False, 0, 0, 0, 0)
#            else:
#                return (False, 0, 0, 0, 0)

        x,y,w,h = [frects[0][kk] for kk in ['x','y','w','h']]

        if self.savework:
            rectangle = image3.copy()
            cv2.rectangle(rectangle, (x,y),(x+w,y+h), (100,100,100),3)
            self.savedwork['rectangle'] = rectangle
        x += xOffset

        # Print the size and location of the white square
        self.logger.debug(f'White square size: {w}x{h} pixels')
        self.logger.debug(f'White square location: ({x}, {y})')

        if self.savework:
            self.savedwork['identified'] = image3.copy()
        if self.saveallwork:
            self.__dumpSaved()

        return (True, x, y, w, h)

    def inccount(self) -> None:
        self.count += 1

    def findfunc(self):
        return self.__findfunc

    def waitSprocket(self, picam, desired:bool) -> None:
        start = time.time()
        while (time.time() - start) < 5.0:
            buffer = picam.capture_array("lores")
#            buffer = cv2.imread('/media/frames/fm110/capture/)
            self.count += 1
#            self.logger.debug(str(picam.capture_metadata()))
            inSprocket = self.__findfunc(buffer)[0]
            self.logger.debug(f'inSprocket {inSprocket}, need {str(desired)}')
            if desired == inSprocket:
                return

        self.__dumpSaved()
        raise RuntimeError('timeout')
