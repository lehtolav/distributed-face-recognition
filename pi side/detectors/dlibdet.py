from threading import Lock
import numpy as np
import cv2
import time
import dlib
from detectors.facedetector import FaceDetector

def dlibMaker():
    detector = dlib.get_frontal_face_detector()
    def detect(frame):
        faces = detector(frame, 1)
        faceList = []
        for face in faces:
            faceList.append((
                face.left(),
                face.top(),
                face.right() - face.left(),
                face.bottom() - face.top()
            ))
        return faceList
    def f(main):
        return FaceDetector(main, detect)
    return f
