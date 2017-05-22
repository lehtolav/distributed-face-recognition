from trackers.facetracker import FaceTracker
from threading import Thread
import cv2
import numpy as np

def camshiftMaker(main, bb):
    termCrit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    auxdata = {}
    lowerBound = np.array([0, 48, 40], dtype = "uint8")
    upperBound = np.array([25, 220, 220], dtype = "uint8")
    conversion = cv2.COLOR_BGR2HSV
    #self.lowerBound = np.array([0, 133, 77], dtype = "uint8")
    #self.upperBound = np.array([255, 173, 127], dtype = "uint8")
    #self.conversion = cv2.COLOR_BGR2YCR_CB
    
    def track(frame, br, bb):
        cvt = cv2.cvtColor(frame, conversion)
        if 'hist' not in auxdata:
            auxdata['mask'] = cv2.inRange(
                cvt,
                lowerBound,
                upperBound
            )
            auxdata['hist'] = cv2.calcHist([cvt], [0], auxdata['mask'], [180], [0, 180])
            cv2.normalize(auxdata['hist'], auxdata['hist'], 0, 255, cv2.NORM_MINMAX)

        dst = cv2.calcBackProject([cvt], [0], auxdata['hist'], [0, 180], 1)
        return cv2.CamShift(dst, bb, termCrit)
    
    newTracker = FaceTracker(main, bb, track)
    Thread(None, newTracker).start()
    main.faceTrackers.append(newTracker)
