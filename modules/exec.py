from modulecommon import *

class Module(irc.IRCClient):

	help = {
		'desc': 'executes a python statement inside the exec module.',
		'exec': {
			'desc': 'executes a given statement.',
			'params': {
				'statement': 'A python statement to execute. For ease of use, self.say refers to a method for printing to the current channel which takes a string argument.'
			}
		}
	}

	def __init__(self, main):
		self.main = main

	def privmsg(self, user, channel, message):
		if channel == self.main.username:
			self.channel = user
		else:
			self.channel = channel
		words = message.split(' ', 1)
		if words[0] == '!exec' and user in self.main.admins:
			print 'Executing: ' + words[1]
			exec words[1]

	def say(self, msg):
		self.main.msg(self.channel, msg, MSGHACK)
