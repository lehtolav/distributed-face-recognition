# distributed-face-recognition
A distributed face recognition system made as part of my work at my university.

The different sides of the program are installed on remote devices. The Pi side program sends facial images from a video stream captured by a pi camera/webcam etc.

The server side receives and saves the images, and optionally classifies them, sending the classification back to the Pi side.

For now, any directories (e.g. the one to save the facial images in) are hardcoded and have to be adjusted from the source files.

The Pi side program was used on a Raspberry Pi 3, but should work with any device with a webcam and a linux based OS.


Pi side program depends NumPy and OpenCV installed with the tracker community contribution addon.

Server side program depends on OpenCV, Openface, DLib and NumPy
