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

class FaceDetector():
    def __init__(self, mainObj, detector, queue = None, extrap = 0):
        self.faceLock = Lock()
        self.mainObj = mainObj
        self.quit = False
        self.detector = detector
        self.faces = []
        self.extrap = extrap
        self.queue = queue
        self.lastTime = 0

    def __call__(self):
        self.faceLoop()
        print 'Detector exiting'

    def faceLoop(self):
        while not self.quit:
            if self.queue is not None:
                with self.queue:
                    self.queue.wait()
            frame = self.mainObj.getCopyOfFrame()
            startTime = time.clock()
            newFaces = self.detector(frame)
            (maxw, maxh) = self.mainObj.getWindowSize()
            for index, (x, y, w, h) in enumerate(newFaces):
                extraw = self.extrap * w
                extrah = self.extrap * h
                left = np.int0(max(x - extraw, 0))
                right = np.int0(min(x + w + extraw, maxw))
                top = np.int0(max(y - extrah, 0))
                bottom = np.int0(min(y + h + extrah, maxh))
                newFaces[index] = (left, top, right - left, bottom - top)
            with self.faceLock:
                self.faces += list(newFaces)
            self.lastTime = time.clock() - startTime

    def processFaces(self, process):
        with self.faceLock:
            self.faces = process(self.faces)

    def stop(self):
        self.quit = True
