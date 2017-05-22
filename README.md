# distributed-face-recognition
A distributed face recognition system made as part of my masters thesis.

The different sides of the program are installed on remote devices. The Pi side program sends facial images from a video stream captured by a pi camera/webcam etc.

The server side receives and saves the images, and optionally classifies them, sending the classification back to the Pi side.

The Pi side program was used on a Raspberry Pi 3, but should work with any device with a webcam.
