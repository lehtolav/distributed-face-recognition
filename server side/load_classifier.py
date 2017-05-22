import socket
import messager
import sys

# Connects to port 8989. This needs to be changed for classification server as well if needed.
# Currently only connects to loopback. Note that this only commands the server to load the specified
# classifier: the argument is the classifiers path on the server. No file is transferred.

sock = socket.socket()
sock.connect(('127.0.0.1', 8989))

messager.send_message(sock, 'new_classifier', sys.argv[1])
