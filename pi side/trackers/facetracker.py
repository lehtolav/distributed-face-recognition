#Face tracker
#  Queue in NewFrameAvailable lock.
#  Increment 'Using current frame' counter (semaphore or locked variable)
#  Release NewFrameAvailable lock
#  if not first frame, do tracking
#  if face missing: stop using frame and set a flag to true to indicate self destruction (stop thread)
#  queue for drawing to current frame and draw a bounding box
#  release frame from use
#  Send face to host
#  check mailbox for label

from threading import Lock, Thread
import cv2
import numpy as np
import time
import uuid
import pickle

class FaceTracker:
    # mainObj refers to the TrackerMain object
    # that provides frames for proessing
    def __init__(self, mainObj, bb, track):
        self.quit = False
        self.mainObj = mainObj
        self.bbLock = Lock()
        self.bb = tuple(bb)
        self.br = None # Bounding rectangle
        self.track = track
        self.label = None
        self.lastSend = time.clock()
        self.id = str(uuid.uuid4())
        mainObj.register(self, True)
        mainObj.sendMessage('register', self.id)

    def __del__(self):
        self.mainObj.sendMessage('unregister', self.id)
        mainObj.register(self, False)

    def __call__(self):
        self.trackLoop()
        print 'Tracker exiting'

    # Runs the tracker
    def trackLoop(self):
        while not self.quit:
            newFrame = self.mainObj.getReadWriteFrame()

            tic = time.clock()
            (self.br, self.bb) = self.track(newFrame, self.br, self.bb)
            print 'tracking took ' + str(time.clock() - tic)

            self.mainObj.freeReadWriteFrame()

            if self.bb[2] <= 0 or self.bb[3] <= 0:
                print self.bb
                self.quit = True
            elif time.clock() - self.lastSend > 0.25:
                scale = 1 / self.mainObj.trackerFrameSize
                (x, y, w, h) = np.int0(tuple(i * scale for i in self.bb))
                crop = self.mainObj.fullFrame[y:(y+h), x:(x+w)]
                self.mainObj.sendMessage(str(self.id), pickle.dumps(crop))
                self.lastSend = time.clock()

    # Gets the current boundingbox
    def getBB(self):
        with self.bbLock:
            return self.bb

    def drawBB(self, frame, scale):
        with self.bbLock:
            if False:#self.br:
                pts = cv2.boxPoints(self.br)
                pts = np.int0(pts)
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
            else:
                bb = self.bb
                (x, y, w, h) = np.int0(tuple(i * scale for i in bb))
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                if self.label is not None:
                    thickness = 2
                    ((twidth, theight), _) = cv2.getTextSize(self.label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, thickness)
                    cv2.rectangle(frame, (x, y), (x + twidth + 1, y + theight + 1), (0, 255, 0), -1)
                    cv2.putText(frame, self.label, (x, y + theight), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), thickness)


    def bbOverlap(self, bb):
        (x1, y1, w1, h1) = self.bb
        (x2, y2, w2, h2) = bb
        selfarea = w1 * h1
        otherarea = w2 * h2
        sharedarea = float(min(selfarea, otherarea))
        if sharedarea == 0:
            return 1 # Full overlap, e.g. remove one tracker
        left = max(x1, x2)
        right = max(left, min(x1 + w1, x2 + w2))
        top = max(y1, y2)
        bottom = max(top, min(y1 + h1, y2 + h2))
        overlap = float(right - left) * float(bottom - top) / sharedarea
        print overlap
        return overlap

    def setLabel(self, sock, newLabel):
        if newLabel == '#lost#' or newLabel == 'negative':
            self.quit = True
        else:
            self.label = newLabel

    def stop(self):
        self.quit = True
