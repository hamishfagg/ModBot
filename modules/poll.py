from modulecommon import *
import MySQLdb as mysql

class Module(irc.IRCClient):

	def __init__(self, main):
		self.main = main
		
		self.db = mysql.connect(host="localhost", user="ircuser", passwd="ctg01", db="chaostheory")
		self.cur = self.db.cursor()
		self.updateCurrent()
	
	def updateCurrent(self):
		self.cur.execute("""SELECT * FROM polls WHERE `closed` = 0""")
		self.current = self.cur.fetchone()

	def closePoll(self):
		if self.current == None:
			return
		self.cur.execute("""UPDATE `polls` SET `closed` = CURRENT_TIMESTAMP WHERE `id` = %s""", (self.current[0],))
		self.main.say(self.main.factory.channel, "The poll has been closed!", MSGHACK)
		self.main.say(self.main.factory.channel, self.current[2], MSGHACK)
		self.main.say(self.main.factory.channel, "Results:%s votes to%s." % (chr(3) + '3 ' + str(self.current[3]) + chr(3) + '1', chr(3) + '4 ' + str(self.current[4]) + chr(3) + '1'), MSGHACK)
		self.current = None

	def privmsg(self, user, channel, message):
		self.db.ping(1)
		words = message.split(' ', 1)
		if user in self.main.admins:
			if words[0] == '!newpoll' and len(words) > 1:
				self.closePoll()
				self.cur.execute("""INSERT INTO `polls` (`user`, `poll`) VALUES (%s, %s)""", (user, words[1]))
				self.updateCurrent()
				self.main.say(self.main.factory.channel, "There is a new poll: %s" % self.current[2], MSGHACK)
				self.main.say(self.main.factory.channel, "Type '!vote yes' or '!vote no' to vote.", MSGHACK)
				
			if words[0] == '!closepoll':
				if self.current == None:
					self.main.say(self.main.factory.channel, "%sThere is currently no poll." % self.main.colour, MSGHACK)
				else:
					self.closePoll()
				
				
		if words[0] == '!poll':
			if self.current == None:
				self.main.say(self.main.factory.channel, "%sThere is currently no poll." % self.main.colour, MSGHACK)
				return
			self.main.say(self.main.factory.channel, "The current poll is: %s" % self.current[2], MSGHACK)
			self.main.say(self.main.factory.channel, "Current votes:%s /%s." % (chr(3) + '3 ' + str(self.current[3]) + chr(3) + '1', chr(3) + '4 ' + str(self.current[4]) + chr(3) + '1'), MSGHACK)			
			self.main.say(self.main.factory.channel, "Type '!vote yes' or '!vote no' to vote.", MSGHACK)
		
		if words[0] == '!vote':
			if self.current == None:
				self.main.say(self.main.factory.channel, "%sThere is currently no poll." % self.main.colour, MSGHACK)
				return
			if self.cur.execute("""SELECT * FROM `votes` WHERE (`user` = %s OR `host` = %s) AND `poll_id` = %s LIMIT 1""", (user, self.main.host, self.current[0])):
				self.main.say(self.main.factory.channel, "%sYou have already voted on this poll." % self.main.colour, MSGHACK)
				return
			if words[1] == 'yes':
				self.cur.execute("""UPDATE `polls` SET `yes` = %s WHERE id = %s""", (self.current[3] + 1, self.current[0]))
				ret = self.cur.execute("""INSERT INTO `votes` (`poll_id`, `user`, `host`, `vote`) VALUES (%s, %s, %s, 1)""", (str(self.current[0]), user, self.main.host))
				self.updateCurrent()
			elif words[1] == 'no':
				self.cur.execute("""UPDATE `polls` SET `no` = %s WHERE id = %s""", (self.current[4] + 1, self.current[0]))
				ret = self.cur.execute("""INSERT INTO `votes` (`poll_id`, `user`, `host`, `vote`) VALUES (%s, %s, %s, 0)""", (self.current[0], user, self.main.host))
				self.updateCurrent()
			else:
				return
			self.main.msg(channel, "%sYour vote has been cast." % self.main.colour, MSGHACK)
