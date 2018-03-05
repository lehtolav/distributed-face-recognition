# Defines procedures for pruning and processing bounding boxes produced by
# the haar cascade detector

import cv2
import itertools
import numpy as np

# Shows rectangles around faces, but does not initiate trackers
def showBoxes(main):
    def shower(faces):
        for bb in faces:
            (x, y, w, h) = np.int0(tuple(i / main.detectorFrameSize for i in bb))
            cv2.rectangle(main.writeFrame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        # Seems I intended to return a list of boundingboxes, but changed the implementation
        return []

    return shower

# Uses an overlapping threshold to determine if a new tracker should be launched for a face detection
def pruneAndAdd(threshold):
    def f(main):
        def aux(faces):
            filtered = []
            for i in range(len(main.faceTrackers)):
                if all(b.bbOverlap(main.faceTrackers[i].bb) < threshold for b in (main.faceTrackers[j] for j in range(i + 1, len(main.faceTrackers)))):
                    if not main.faceTrackers[i].quit:
                        filtered.append(main.faceTrackers[i])
                else:
                    print 'filtered'
                    main.faceTrackers[i].stop()
            main.faceTrackers = filtered

            rate = main.trackerFrameSize / main.detectorFrameSize
        
            for bb in faces:
                bb = np.int0(tuple(i * rate for i in bb))
        
                if all(tracker.bbOverlap(bb) < threshold
                       for tracker in main.faceTrackers):
                    main.makeNewFaceTracker(bb)
            return []
        return aux
    return f
