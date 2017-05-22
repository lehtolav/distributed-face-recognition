from trackers.facetracker import FaceTracker
from threading import Thread
import cv2
import numpy as np

def CVTrackerMaker(trackerType):
    def maker(main, bb):
        auxdata = {}
    
        def track(frame, br, bb):
            if 'tracker' not in auxdata:
                auxdata['tracker'] = cv2.Tracker_create(trackerType)
                auxdata['tracker'].init(frame, bb)
            else:
                _, bb = auxdata['tracker'].update(frame)
            return (None, bb)
    
        newTracker = FaceTracker(main, bb, track)
        Thread(None, newTracker).start()
        main.faceTrackers.append(newTracker)

    return maker
