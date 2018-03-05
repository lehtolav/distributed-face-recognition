#Main thread:
#  Lock NewFrameAvailable lock.
#  Loop:
#    See if the face detector has new faces to add.
#    Camera takes a picture.
#    The main thread waits until all other threads have finished using the previous frame.
#    The previous frame is rendered (with any modifications).
#    Initiate new face trackers.
#    Replace old frame.
#    Release NewFrameAvailable lock.
#    Process network messages
#    Lock NewFrameAvailable lock.

# It turned out that locks don't allow for queuing in order
# (threads are notified in random order)
# For this reason, some network processing is done between
# releasing and reacquiring the NewFrameAvailable lock to allow
# trackers and detectors to work with the frame

from threading import Lock, Condition, Thread
import socket
import numpy as np
import messager
import cv2
import bbprocessors
from time import sleep, clock
import random

class TrackerMain():
    def __init__(self, address, port, trackerMaker, detectorMaker, bbProcessor, multiDetect=0, width=320, height=240, detectorFrameSize=1, trackerFrameSize=1, backwardsConnection=False):
        self.newFrameAvailable = Lock() # Queue for usage of new frame
        self.usingCurrentFrame = Condition() # Lock when writing to frame
        self.netLock = Lock() # Lock for sending network messages
        self.frameUsers = 0 # Number of threads wanting to write eventually
        self.faceTrackers = []
        self.faceDetectors = []
        self.bbProcessor = bbProcessor(self)
        self.newFrameAvailable.acquire()

        self.messager = messager.Messager()

        # Connect to remote messager
        # A possibility for backwards connection was necessary for security reasons
        if not backwardsConnection:
            #self.messageSock = socket.socket()
            #self.messageSock.connect((address, port))
            self.messageSock = self.messager.connect(address, port)
        else:
            # With backwards connection we need to wait for the connection
            self.messager.setupHost(address, port)
            self.start = False
            self.messager.register('connect', self.setHost)
            while not self.start:
                self.messager.processHost()
            self.messager.unregister('connect')
        
        if multiDetect > 0:
            # Setup queue for multiple detectors
            # Detectors will be notified one at a time
            # at intervals of average detection time
            self.detectionQueue = Condition()
            self.avgDetTime = 0 # average time to run a detector
            self.avgDetSamples = 0 # N of samples in the average
            self.multiDetect = True
        else:
            multiDetect = 1
            self.multiDetect = False

        # Make the face detectors
        for i in range(0, multiDetect):
            newDetector = detectorMaker(self)
            self.faceDetectors.append(newDetector)
            Thread(None, newDetector).start()

        # Setup camera
        self.videoCapture = cv2.VideoCapture(0)
        self.videoCapture.set(3, width) # Width
        self.videoCapture.set(4, height) # Height
        self.maxw = self.videoCapture.get(3)
        self.maxh = self.videoCapture.get(4)
        ret, frame = self.videoCapture.read()
        self.readFrame = frame
        self.writeFrame = np.copy(frame)

        # Setup preview window
        self.windowName = 'Video'
        self.window = cv2.namedWindow(self.windowName)

        # Register trackerMaker
        # This creates new trackers, e.g. starts tracking threads
        # or does nothing if tracker threads are not wanted
        # It also defines the type of tracker to use
        self.trackerMaker = trackerMaker

        self.detectorFrameSize = detectorFrameSize
        self.trackerFrameSize = trackerFrameSize

        self.startTime = clock()

        # FPS calculation
        self.fps = 0.0
        self.fpsSamples = 100
        self.frameTimes = [0.0] * self.fpsSamples
        self.curSample = 0
        self.lastTime = clock()

    def mainLoop(self):
        # Note: this thread should have aquired the newFrameAvailable
        # lock before entering this method.
        # The first acquisition is in the class constructor.

        # See if there are any new faces waiting
        averageTime = 0
        for detector in self.faceDetectors:
            detector.processFaces(self.bbProcessor)
            averageTime += detector.lastTime

        averageTime /= len(self.faceDetectors)

        ret, frame = self.videoCapture.read()

        # Wait until all trackers are finished with the previous frame
        with self.usingCurrentFrame:
            if self.frameUsers > 0:
                self.usingCurrentFrame.wait()

        # Draw boundingboxes and labels (when available) on the image
        for tr in self.faceTrackers:
            tr.drawBB(self.writeFrame, 1 / self.trackerFrameSize)

        # Calculate and display FPS
        newTime = clock()
        fps = 1.0 / float(newTime - self.lastTime)
        self.lastTime = newTime
        self.fps -= self.frameTimes[self.curSample]
        self.fps += fps
        self.frameTimes[self.curSample] = fps
        self.curSample = (self.curSample + 1) % self.fpsSamples
        cv2.putText(self.writeFrame, str(float(self.fps)/float(self.fpsSamples)), (0, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Show previous frame
        cv2.imshow(self.windowName, self.writeFrame)

        # Replace old frames
        self.fullFrame = frame
        self.readFrame = cv2.resize( frame
                                   , (0, 0)
                                   , fx=self.trackerFrameSize
                                   , fy=self.trackerFrameSize
                                   )
        self.writeFrame = np.copy(frame)

        # See if we should notify a detector
        if self.multiDetect:
            elapsedTime = clock() - self.startTime
            if elapsedTime >= averageTime / len(self.faceDetectors):
                self.startTime = clock()
                with self.detectionQueue:
                    self.detectionQueue.notify()
        
        # Let other threads use the current frame for a while
        self.newFrameAvailable.release()
        self.messager.processHost()
        tic = clock()
        self.newFrameAvailable.acquire()
        
    def stop(self):
        if self.multiDetect:
            with self.detectionQueue:
                self.detectionQueue.notify_all()
        for fd in self.faceDetectors:
            fd.stop()
        for ft in self.faceTrackers:
            ft.stop()
        self.newFrameAvailable.release()

    def getCopyOfFrame(self):
        with self.newFrameAvailable:
            return cv2.resize( self.fullFrame
                             , (0, 0)
                             , fx=self.detectorFrameSize
                             , fy=self.detectorFrameSize
                             )

    def getReadWriteFrame(self):
        with self.newFrameAvailable:
            with self.usingCurrentFrame:
                self.frameUsers += 1
            return self.readFrame

    def freeReadWriteFrame(self):
        with self.usingCurrentFrame:
            self.frameUsers -= 1
            if self.frameUsers == 0:
                self.usingCurrentFrame.notifyAll()

    def applyToFrame(self, f):
        with self.usingCurrentFrame:
            f(self.writeFrame)

    def makeNewFaceTracker(self, bb):
        # Invoke closure
        self.trackerMaker(self, bb)

    def sendMessage(self, messagetype, message):
        tic = clock()
        with self.netLock:
            messager.send_message(self.messageSock, messagetype, message)

    def register(self, tracker, add):
        if add:
            self.messager.register(tracker.id, tracker.setLabel)
        else:
            self.messager.unregister(tracker.id)

    def getWindowSize(self):
        return (self.maxw, self.maxh)

    def setHost(self, sock, msg):
        self.messageSock = sock
        self.start = True
