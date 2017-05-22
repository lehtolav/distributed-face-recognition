#Face detector
#  Lock faces available lock.
#  Successful:
#    Grab the current frame.
#    Find faces.
#    Release faces available lock.
#  Unsuccessful:
#    Wait a short time and try again
#
#  notes:
#    After fetching the faces, the main thread must empty the new faces list

from threading import Lock
import numpy as np
import cv2
import time
from detectors.facedetector import FaceDetector

def haarMaker(cascPath):
    cascade = cv2.CascadeClassifier(cascPath)
    def detect(frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        newFaces = cascade.detectMultiScale(
                frame,
                scaleFactor=1.1,
                minNeighbors=1,
                minSize=(5, 5),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
        return newFaces
    def f(main):
        return FaceDetector(main, detect)
    return f
