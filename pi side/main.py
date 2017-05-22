import threading as th
from trackermain import TrackerMain
import detectors.haar
# Enable if you want to try the dlib detector
# Commenting this out should remove the dlib dependency
#import detectors.dlibdet
import trackers.camshift
import trackers.cvtracker
import bbprocessors
import sys
import cv2

cascPath = sys.argv[1]
def noTracking(s, bb):
    pass

# Which tracker to use
# Possible values:
#  noTracking (no trackers are initialized / detection only)
#  trackers.camshift.camshiftMaker
#  trackers.cvtracker.CVTrackerMaker(type)
#   (types: BOOSTING, MIL, MEDIANFLOW, KCF, TLD, GOTURN (runs out of memory)
tracker = trackers.cvtracker.CVTrackerMaker('KCF')

# Which object detection to use
# dlib detector seems bad
# Possible values
#  detectors.dlibdet.dlibMaker()
#  detectors.haar.haarMaker(cascPath)
#   (path to the cascade model to use)
detector = detectors.haar.haarMaker(cascPath)

# Which bounding box processor to use
# Possible values
#  bbprocessors.pruneAndAdd(x)
#   (prunes bbs that overlap too much
#    (argument is the maximum allowed overlap as Jaccard index))
#  bbprocessors.showBoxes
#   (only shows boxes for detections: does not initialize trackers)
bbprocessor = bbprocessors.pruneAndAdd(0.3)

main = TrackerMain(
    '169.254.148.248', # IP for host if forward connection, self if backward
    8292, # port
    tracker,
    detector,
    bbprocessor,
    0,
    640,
    480,
    1./4.,
    1./8.,
    False # Whether to use a backwards connection (server contacts client)
    )

try:
    while True:
        main.mainLoop()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    main.stop()

