from constants import *

class Module():

	commands = {'say': 'say'}

	def say(self, user, channel, args):
		if channel == user:
			if args[0] in self.main.channels:
				if user in self.main.channels[args[0]]['admins']:
					self.main.msg(self.main.channel, " ".join(args), MSG_MAX)
			else:
				self.main.msg(channel, "I'm not on %s." % args[0])
