### Distributed face recognition, Raspberry Pi side program

Edit main.py to setup IPs.

usage:
python main.py cascadefile

where the cascade file determines the Haar cascade model file for object detection.


OpenCV has some [models](https://github.com/opencv/opencv/tree/master/data) for download.


The program uses a Haar cascade to detect faces in the video stream and launches trackers to track them in separate threads.
Each tracker can also tag their target with a classification if one is sent to them by the server program.
