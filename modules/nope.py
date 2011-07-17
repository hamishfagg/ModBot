from modulecommon import *

class Module(irc.IRCClient):
	
	def __init__(self,  main):
		self.main= main

	def privmsg(self, user, channel, msg):
		if msg.startswith('!'):
			msg = msg[1:]
		if msg.lower().startswith('nope.avi'):
			self.main.say(self.main.factory.channel, 'http://www.youtube.com/watch?v=gvdf5n-zI14', MSGHACK)
		elif msg.lower().startswith('brilliant!'):
			self.main.say(self.main.factory.channel, 'http://www.youtube.com/watch?v=NBh895KdXAU', MSGHACK)
			
