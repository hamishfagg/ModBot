from constants import *

class Module():

	commands = {'say': 'say'}

	def say(self, user, channel, args):
		if channel != self.main.factory.channel and user in self.main.admins:
			self.main.msg(self.main.factory.channel, " ".join(args), MSG_MAX)
		
