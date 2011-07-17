from modulecommon import *
import MySQLdb as mysql

class Module(irc.IRCClient):

	def __init__(self, main):
		self.main = main
		self.db = mysql.connect(host='localhost', user='ircuser', passwd='ctg01', db='chaostheory')
		self.cur = self.db.cursor()

	def privmsg(self, user, channel, message):
		words = message.split()

		if words[0] == '!stats':
			if len(words) == 1:
				pass #general stats
			elif len(words) == 2:
				pass #general user stats
			elif len(words) == 3:
				pass #user stats of type words[2]
