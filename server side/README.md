### Distributed face recognition, server side program

Edit main.py to setup IPs.

Then simply run:  
python main.py

The program saves facial images from the sensor device to a predefined folder, which is currently hardcoded in classification\_server\.py

To train classifiers, you can use the training program from openface (classifier.py in demos folder).

To load a classifier run:  
python load\_classifier.py path\_to\_classifier  
while the server is running.
