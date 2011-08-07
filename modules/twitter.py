from constants import *
import twitterhandler

class Module():

	depends = ['log']
	commands = {'tweet': 'tweet'}
	help = {
		'desc': 'tweets things from chan to the ChaosTheory twitter account - ChaosTheoryServ',
		'tweet': {
			'desc': 'Tweets the supplied message.',
			'params': {
				'message': 'String to tweet. Must be 140 characters or less.'
			}
		}
	}

	def tweet(self, user, channel, args):
		tweet = " ".join(args)
		if user in self.main.admins:
			if len(tweet) > 140:
				self.main.say(self.main.factory.channel, "%sTweet too long, please shorten it by %s characters." % (self.main.colour, len(tweet) - 140), MSG_MAX)
			else:	
				if twitterhandler.tweet(tweet):
					self.main.say(self.main.factory.channel, "%sSent tweet." % self.main.colour, MSG_MAX)
				else:
					self.main.say(self.main.factory.channel, "%sSending tweet failed. Check logs for details." % self.main.colour, MSG_MAX)
			
	def tweetQuote(self, quote):
		if len(quote) > 140:
			self.main.say(self.main.factory.channel, "%sCouldn't tweet that quote - it's too long. You need to shorten it by %s characters." % (self.main.colour, len(quote) - 140), MSG_MAX)
		elif not twitterhandler.tweet(quote):
			self.main.say(self.main.factory.channel, "%sSending quote tweet failed. Check logs for details." % self.main.colour, MSG_MAX)

