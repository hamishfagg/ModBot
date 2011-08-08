from constants import *
import time

class Module():
	hooks = {'loaded': 'loaded',
			 'joined': 'joined',
			 'userjoined': 'userJoined',
			 'modechanged': 'modeChanged',
			 'noticed': 'noticed'}
	def loaded(self):
		if self.main.inchannel: self.joined(None)

	def getStatus(self, user):
		self.main.msg('nickserv', "status %s" % user, MSG_MAX)
		
	def joined(self, channel):
		for user in self.main.users:
			if not (user in self.main.admins) and user != self.main.nickname:
				self.getStatus(user)

	def userJoined(self, user, channel):
		user = user.split('!', 1)[0]
		if not (user in self.main.admins) and user != self.main.nickname:
			self.getStatus(user)

	def modeChanged(self, user, channel, set, modes, args):
		user = user.split('!', 1)[0]
		if modes == 'r' and not (user in self.main.admins) and user != self.main.nickname:
			if set:
				self.main.mode(self.main.factory.channel, True, 'v', None, user)				
			else:
				self.main.mode(self.main.factory.channel, False, 'v', None, user)

	def noticed(self, user, channel, message):
		words = message.split()
		if user.split('!', 1)[0] == 'NickServ' and words[0] == 'STATUS' and words[2] == '3':
			self.main.mode(self.main.factory.channel, True, 'v', None, words[1])

