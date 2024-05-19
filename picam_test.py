#!/usr/bin/env python3

import cv2
from libcamera import Transform
from picamera2 import Picamera2, Preview
import time

global picam

def init_preview():
    picam = Picamera2()
    picam.start_preview(Preview.QTGL)
    controls={'FrameDurationLimits':(100000,100000),'ExposureTime': 65000,
              'AeEnable': False, 'AwbEnable': False, 'AnalogueGain': 1.0}
    picam.configure(picam.create_preview_configuration(controls=controls))
    picam.start()

def setExposure(picam, exposure):
    picam.set_controls({'ExposureTime': exposure, 'AnalogueGain': 8.0})
    start = time.time()
    while (time.time() - start) < 1.0:
        picam.capture_array("lores")
        camexp = picam.capture_metadata()['ExposureTime'] 
        print(f'Got {camexp}, want {exposure}')
        if int(exposure * 0.8) < camexp < int(exposure * 1.1):
            return
    raise RuntimeError('timeout')

def init_still():
    lores={"size":(640,480),"format":"RGB888"}
    main={"size":(2304,1296),"format":"RGB888"}

    controls={'FrameDurationLimits':(100000,100000),'ExposureTime': 65000,
              'AeEnable': False, 'AwbEnable': False}
    transform = Transform(hflip=True)

    picam = Picamera2()
#    cam_config = picam.create_video_configuration(queue=False,main=main,lores=lores,transform=transform,controls=controls)
    cam_config = picam.create_still_configuration()

    Picamera2.set_logging(Picamera2.DEBUG)
    picam.set_controls({'ExposureTime': exposure, 'AnalogueGain': 8.0})
#        pdb.set_trace()
#        aa = picam.camera_controls()

#    picam.configure(cam_config)
#    picam.align_configuration(cam_config)
#    picam.start_preview(Preview.QTGL)
    picam.start(show_preview=True)

def click():
    pass

def main():
    init_still()
    time.sleep(10)
    pass

main()
