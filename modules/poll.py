from constants import *
from datetime import datetime

class Module():

	depends = ['log', 'mysql']
	hooks = {'loaded': 'loaded'}
	commands = {'closepoll': 'closePoll',
				'poll': 'poll',
				'newpoll': 'newPoll',
				'vote': 'vote'}

	def loaded(self):
		self.mysql.connect('polls')
		self.updateCurrent()
	
	def updateCurrent(self):
		self.current = self.mysql.execute("SELECT * FROM polls WHERE `closed` = 0 LIMIT 1")
		if len(self.current) == 0: self.current = None
		else: self.current = self.current[0]

	def poll(self, user, channel, args):
		if self.current == None:
			self.main.say(channel, "There is currently no poll.", MSG_MAX)
		else:
			self.main.say(channel, "The current poll is: %s" % self.current[2], MSG_MAX)
			self.main.say(channel, "Current votes:%s %s%s /%s %s%s." % (COLOUR_GREEN, str(self.current[3]), COLOUR_DEFAULT, COLOUR_RED, str(self.current[4]), COLOUR_DEFAULT), MSG_MAX)			
			self.main.say(channel, "Type '!vote yes' or '!vote no' to vote.", MSG_MAX)

	def closePoll(self, user, channel, args):
		if self.current != None:
			self.mysql.update(data={'closed': datetime.now()}, conditions={'id': self.current[0]})
			self.main.say(self.main.factory.channel, "The poll has been closed!", MSG_MAX)
			self.main.say(self.main.factory.channel, self.current[2], MSG_MAX)
			self.main.say(self.main.factory.channel, "Results:%s %s%s votes to%s %s%s." % (COLOUR_GREEN, str(self.current[3]), COLOUR_DEFAULT, COLOUR_RED, str(self.current[4]), COLOUR_DEFAULT), MSG_MAX)
			self.current = None
		else:
			self.main.msg(channel, "There is currently no poll.", MSG_MAX)

	def newPoll(self, user, channel, args):
		poll = " ".join(args)
		if user in self.main.admins:
			if len(poll) != 0:
				self.closePoll(None, None, None)
				self.mysql.insert(data={'user': user, 'poll': poll})
				self.updateCurrent()
				self.main.say(self.main.factory.channel, "There is a new poll: %s" % self.current[2], MSG_MAX)
				self.main.say(self.main.factory.channel, "Type '!vote yes' or '!vote no' to vote.", MSG_MAX)

	def vote(self, user, channel, args):
		if self.current == None:
			self.main.say(channel, "There is currently no poll.", MSG_MAX)
		elif len(self.mysql.find(table='votes', conditions={'user': user, 'poll_id': self.current[0]}, limit=1)) != 0:
			self.main.say(channel, "You have already voted on this poll.", MSG_MAX)
		elif args[0].lower() == 'yes' or args[0].lower() == 'no':
			if args[0].lower() == 'yes':
				votetype = 'yes'
				num = self.current[3] + 1
				vote = 1
			else:
				votetype = 'no'
				num = self.current[4] + 1
				vote = 0

			self.mysql.update(data={votetype: num}, conditions={'id': self.current[0]})
			self.mysql.insert(table='votes', data={'poll_id': str(self.current[0]), 'user': user, 'host': self.main.host, 'vote': vote})
			self.updateCurrent()
			self.main.msg(channel, "Your vote has been cast.", MSG_MAX)
