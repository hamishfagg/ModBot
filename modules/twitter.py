from modulecommon import *
import twitterhandler

class Module(irc.IRCClient):

	help = {
		'desc': 'tweets things from chan to the ChaosTheory twitter account - ChaosTheoryServ',
		'tweet': {
			'desc': 'Tweets the supplied message.',
			'params': {
				'message': 'String to tweet. Must be 140 characters or less.'
			}
		}
	}

	def __init__(self, main):
		self.main = main

	def privmsg(self, user, channel, message):
		words = message.split(' ', 1)
		if user in self.main.admins:
			if words[0] == '!tweet':
				if len(words) > 1 and len(words[1]) > 140:
					self.main.say(self.main.factory.channel, "%sTweet too long, please shorten it by %s characters." % (self.main.colour, len(words[1]) - 140), MSGHACK)
					return
				if twitterhandler.tweet(words[1]):
					self.main.say(self.main.factory.channel, "%sSent tweet" % self.main.colour, MSGHACK)
				else:
					self.main.say(self.main.factory.channel, "%sSending tweet failed. Check logs for details." % self.main.colour, MSGHACK)
			
	def tweetQuote(self, quote):
		if len(quote) > 140:
			self.main.say(self.main.factory.channel, "%sCouldn't tweet that quote - it's too long. You need to shorten it by %s characters." % (self.main.colour, len(quote) - 140), MSGHACK)
		elif not twitterhandler.tweet(quote):
			self.main.say(self.main.factory.channel, "%sSending quote tweet failed. Check logs for details." % self.main.colour, MSGHACK)

