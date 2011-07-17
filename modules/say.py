from modulecommon import *

class Module(irc.IRCClient):

	def __init__(self, main):
		self.main = main

	def privmsg(self, user, channel, message):
		if channel == self.main.nickname and user in self.main.admins:
			words = message.split(' ', 1) #This is done here to save doing it if the above criteria aren't met
			if words[0] == '!say':
				self.main.say(self.main.factory.channel, words[1], MSGHACK)
		
