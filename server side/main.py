import classification_server as cs

# If backwards = False, use own IP (what network card to use)
# If backwards = True, use remote IP (where to connect)
#  Not 100% sure how this determines which (own) network card to use,
#  possibly by routing (knowing where the destination IP is) or some system default,
#  but it seems to work. The socket library allows defining the local IP explicitly if needed.
server = cs.ClassificationServer('169.254.148.248', 8292, backwards = False)

while True:
	server.mainLoop()
