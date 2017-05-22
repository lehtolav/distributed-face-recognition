# Trades messages with a remote host/client
# Essentially provides a layer to transform generic socket datastreams
# into messages (strings) with messagetypes
# Messagetype will be used to invoke a registered callback for that type
# with the message content as its argument

import socket
import select
import struct

mode = "I"
length_size = struct.calcsize(mode)

def recv_message(sock):
	data = sock.recv(length_size, socket.MSG_WAITALL)
	if not data:
		return None, None
	msg_size = struct.unpack(mode, data)[0]
	messagetype = ''
	if msg_size > 0:
                messagetype = sock.recv(msg_size, socket.MSG_WAITALL)
	data = sock.recv(length_size, socket.MSG_WAITALL)
	msg_size = struct.unpack(mode, data)[0]
	message = ''
	if msg_size > 0:
                message = sock.recv(msg_size, socket.MSG_WAITALL)
	print messagetype
	return messagetype, message

def send_message(sock, messagetype, message):
        try:
                mtl = struct.pack(mode, len(messagetype))
                mcl = struct.pack(mode, len(message))
                sock.sendall(mtl + messagetype + mcl + message)
        except socket.error, e:
                print 'Error sending data'
                print e

class Messager():
	def __init__(self):
		self.clients = []
		self.callbacks = dict()
		self.listening = False

	def __del__(self):
		if self.listening:
			self.hostSock.close()
		for sock in clients:
			sock.close()

	def setupHost(self, address, port):
		self.hostSock = socket.socket()
		self.hostSock.bind((address, port))
		self.hostSock.listen(5)
		self.hostSock.setblocking(0)
		self.listening = True

	def processHost(self):
		try:
			if self.listening:
				conn, address = self.hostSock.accept()
				self.clients.append(conn)
		except socket.timeout:
			pass
		except socket.error, e:
			if e[0] == 11:
				pass
			else:
				print e
		inputs, outputs, errors = select.select(self.clients, [], self.clients, 0)
		for sock in inputs:
			messagetype, message = recv_message(sock)
			if messagetype is None:
				self.clients.remove(sock)
				sock.close()
			elif messagetype in self.callbacks:
				self.callbacks[messagetype](sock, message)
		for sock in errors:
			self.clients.remove(sock)
			sock.close()

#	def send(self, target, messagetype, message):
#		pass

	def register(self, messagetype, callback):
		self.callbacks[messagetype] = callback

	def unregister(self, messagetype):
		del self.callbacks[messagetype]

	def connect(self, remoteHost, remotePort):
		# Connect to a remote host and add its socket to the client list
		# i.e. we don't listen for connection, but initiate it
		#This allows two-way communication between two messager objects
		sock = socket.socket()
		sock.connect((remoteHost, remotePort))
		self.clients.append(sock)
		return sock
