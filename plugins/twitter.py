from constants import *
import twitterhandler

class Plugin():

    depends = ['logger']
    commands = {'tweet': 'tweet'}

    def tweet(self, user, args):
        tweet = " ".join(args[1:])
        if user in self.main.admins:
            if len(tweet) > 140:
                self.main.say(self.main.channel, "Tweet too long, please shorten it by %s characters." % (len(tweet) - 140))
            else:
                ret = twitterhandler.tweet(tweet)
                if ret == 1:
                    self.main.msg(self.main.channel, "Sent tweet.")
                else:
                    self.main.msg(self.main.channel, ret)
                    self.logger.log(LOG_ERROR, ret)
            
    def tweetQuote(self, quote):
        if len(quote) > 140:
            self.main.msg(self.main.channel, "Couldn't tweet that quote - it's too long. You need to shorten it by %s characters." % (len(quote) - 140))
        else:
            ret = twitterhandler.tweet(quote)
            if ret != 1:
                self.main.msg(self.main.channel, ret)
                self.logger.log(LOG_ERROR, ret)
