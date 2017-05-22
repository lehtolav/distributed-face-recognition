# High level conceptual view of client/server communication

# The client(s) register objects to track with the trackers UUID
#   messagetype = register, message = UUID
# The client sends face pictures
#   messagetype = UUID, message = image data
# The client reports target lost
#   messagetype = unregister, message = UUID
# The server classifies the target
#   messagetype = UUID, message = class
# The server finds no target (target lost)
#   messagetype = UUID, message = #lost#
# Request a new classifier to be loaded
#   messagetype = new_classifier, message = filename

# Data from targets is gathered to folders named by their UUID
# The folders are processed by a separate program that allows labeling correct classes and true negatives and removal of outliers

import messager
import os
import pickle
import cv2
import openface
import dlib
import numpy as np

class ClassificationServer():
	# Static class members
	mainfolder = '/worktmp/piface/'
	datafolder = mainfolder + 'rawdata/'
	modelfolder = mainfolder + 'models/'

	def __init__(self, localHost, localPort, classPort = 8989, featureModel = 'nn4.small2.v1.t7', alignModel = 'shape_predictor_68_face_landmarks.dat', imageSize = 96, backwards = False):
		self.messager = messager.Messager()
		self.messager.setupHost('127.0.0.1', classPort)
		if not backwards:
			self.messager.setupHost(localHost, localPort)
		else:
			tempsock = self.messager.connect(localHost, localPort)
			messager.send_message(tempsock, 'connect', '')
			print 'sent connect message'
		self.messager.register('register', self.addSource)
		self.messager.register('unregister', self.delSource)
		self.messager.register('new_classifier', self.loadClassifier)
		self.predictions = dict()
		self.imageSize = 96
		self.classifier = None
		self.featureModel = openface.TorchNeuralNet(
			self.modelfolder + featureModel,
			imgDim=imageSize
			)
		self.align = openface.AlignDlib(self.modelfolder + alignModel)

	def __del__(self):
		#self.sendSock.close()
		for uuid, _ in self.predictions:
			self.cleanup(uuid)

	def addSource(self, sock, message):
		self.predictions[message] = dict() # best predictions
		os.mkdir(self.datafolder + message)
		# Make further messages with this UUID call the image processor
		self.messager.register(message, self.processImage(message))

	def delSource(self, sock, message):
		print 'Removing source'
		del self.predictions[message]
		self.cleanup(message)

	def cleanup(self, uuid):
		self.messager.unregister(uuid)
		# write final prediction of class

	def loadClassifier(self, sock, filename):
		print 'Loading classifier ' + filename
		with open(filename, 'r') as classifier:
		        self.classifier = pickle.load(classifier)

	def processImage(self, uuid):
		predictions = self.predictions[uuid]
		self.nImages = 1
		def process(sock, imagedata):
			# Load image
			image = pickle.loads(imagedata)

			#(w, h) = image.shape
			if image.size == 0:
				return

			image = cv2.resize(image, (self.imageSize, self.imageSize))
			image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

			# Align face
			aligned = self.align.align(
				self.imageSize,
				image,
				dlib.rectangle(0, 0, self.imageSize, self.imageSize),
				landmarkIndices=openface.AlignDlib.INNER_EYES_AND_BOTTOM_LIP
				)

			if aligned is not None:
				# Classify
				prediction = None
				confidence = 0
				negConfidence = 0
				if self.classifier is not None:
					(le, clf) = self.classifier
					rep = self.featureModel.forward(aligned)
					rep = rep.reshape(1, -1)
					predictions = clf.predict_proba(rep).ravel()
				        maxI = np.argmax(predictions)
					prediction = le.inverse_transform(maxI)
				        confidence = predictions[maxI]
					negIndex = le.transform(['negative'])[0]
					negConfidence = predictions[negIndex]

				# Send answer / current best guess
				if prediction is not None:
					print 'Prediction ' + prediction + ', confidence: ' + str(confidence)
					if confidence > 0.9:
						messager.send_message(sock, uuid, prediction)
					elif negConfidence >= confidence and negConfidence > 0.5:
						messager.send_message(sock, uuid, 'negative')

				# Save image to disk
				image = cv2.cvtColor(aligned, cv2.COLOR_RGB2BGR)
		                cv2.imwrite(self.datafolder + uuid + '/' + str(self.nImages) + '.png', image)
				self.nImages += 1
			else:
				# Report target lost
				messager.send_message(sock, uuid, '#lost#')
		return process

	def mainLoop(self):
		self.messager.processHost()
