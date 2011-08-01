import MySQLdb as mysql

class Module():

	depends = ['mysql', 'log']
	commands = {'q': 		'quote',
				'quote':	'quote',
				'rq':		'randQuote',
				'randquote':'randQUote',
				'nq':		'newQuote',
				'newquote': 'newQuote'}
	hooks =    {'loaded': 'loaded'}

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

	def loaded(self):
		self.mysql.connect('quotes')
	
	def quote(self, user, channel, args):
		if len(args) == 0:
			quote = self.mysql.find(fields=['quote'], order="created DESC", limit=1)[0]
			self.main.msg(channel, quote[0], 10000)
		else:
			quotes = self.mysql.find(fields=['quote'], table="quotes WHERE UPPER(`quote`) LIKE UPPER(%s)" % " ".join(args), limit=6)
			for quote in quotes:
				self.main.msg(channel, self.main.colour + quote[0], MSGHACK)
				if i == 4:
					break
			if len(results) > 5:
				self.main.msg(channel, "%sExceeded maximum search results. Try a more specific search" % self.main.colour, MSGHACK)

	def privmsg(self, user, channel, message):
		if channel == self.main.nickname:
			channel = user
		
		words = message.split(' ', 1)

		if words[0] == '!rq' or words[0] == '!randquote':
			#self.cur.execute("""SELECT * FROM quotes ORDER BY rand() LIMIT 1""")
			#self.main.msg(channel, self.cur.fetchone()[2], MSGHACK)
			pass
		if words[0] == '!q' or words[0] == '!quote':
			pass
		
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
