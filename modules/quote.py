from modulecommon import *
import MySQLdb as mysql

class Module(irc.IRCClient):

	help = {
		'desc': 'searches, prints or adds new quotes. Tweets new quotes as they are added (if the Twitter module is loaded)',
		'quote': {
			'desc': 'Searches the quote database given a search term. If none is given, this command prints the latest quote.',
			'params': {
				'searchstring': 'String term to search for in the quote database (optional).'
			}
		},
		'newquote': {
			'desc': 'Adds a new quote to the database. Tweets the new quote given it is short enough and the Twitter module is loaded.',
			'params': {
				'quote': 'Quote to add to the database.'
			}
		},
		'randquote': {
			'desc': 'Prints a random quote.',
			'params': {}
		}
	}

	def __init__(self, main):
		self.main = main

		self.db = mysql.connect(host="localhost", user="ircuser", passwd="ctg01", db="chaostheory")
		self.cur = self.db.cursor()
		self.db.ping()
	
	def privmsg(self, user, channel, message):
		self.db.ping(1)
		if channel == self.main.nickname:
			channel = user
		
		words = message.split(' ', 1)

		if words[0] == '!rq' or words[0] == '!randquote':
			self.cur.execute("""SELECT * FROM quotes ORDER BY rand() LIMIT 1""")
			self.main.msg(channel, self.cur.fetchone()[2], MSGHACK)
		if words[0] == '!q' or words[0] == '!quote':
			if len(words) == 1:
				self.cur.execute("""SELECT * FROM quotes ORDER BY `created` DESC LIMIT 1""")
				self.main.msg(channel, self.cur.fetchone()[2], MSGHACK)
			else:
				self.cur.execute("""SELECT * FROM quotes WHERE UPPER(`quote`) LIKE UPPER(%s) LIMIT 6""", ('%' + words[1] + '%',))
				results = self.cur.fetchall()
				for i in range(0, len(results)):
					self.main.msg(channel, self.main.colour + results[i][2], MSGHACK)
					if i == 4:
						break
				if len(results) > 5:
					self.main.msg(channel, "%sExceeded maximum search results. Try a more specific search" % self.main.colour, MSGHACK)
		
		if words[0] == '!sq' or words[0] == '!nq' or words[0] == '!storequote' or words[0] == '!newquote':
			print user
			if user in self.main.admins:
				try:
					self.cur.execute("""INSERT INTO `quotes` (`user`, `quote`, `created`) VALUES (%s, %s, CURRENT_TIMESTAMP)""",  (user, words[1]))
					self.main.msg(self.main.factory.channel, "%sQuote saved successfully." % self.main.colour, MSGHACK)
					if self.main.modules.get('twitter', None) != None:
						self.main.modules['twitter'].tweetQuote(words[1])
				except:
					self.main.msg(self.main.factory.channel, "%sAn error occured saving that quote: %s" % (self.main.colour, str(sys.exc_info()[1])) , MSGHACK)
			else:
				self.main.msg(self.main.factory.channel, "%sYou're not an admin." % self.main.colour, MSGHACK)
