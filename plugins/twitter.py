from constants import *
import twitterhandler

class Module():

    depends = ['logger']
    commands = {'tweet': 'tweet'}

    def tweet(self, user, channel, args):
        tweet = " ".join(args)
        if user in self.main.channels[channel]['admins']:
            if len(tweet) > 140:
                self.main.say(channel, "Tweet too long, please shorten it by %s characters." % (len(tweet) - 140), MSG_MAX)
            else:
                ret = twitterhandler.tweet(tweet)
                if ret == 1:
                    self.main.say(channel, "Sent tweet.", MSG_MAX)
                else:
                    self.main.say(channel, ret, MSG_MAX)
                    self.logger.log(LOG_ERROR, ret)
            
    def tweetQuote(self, quote):
        if len(quote) > 140:
            self.main.say(self.main.channel, "Couldn't tweet that quote - it's too long. You need to shorten it by %s characters." % (len(quote) - 140), MSG_MAX)
        else:
            ret = twitterhandler.tweet(quote)
            if ret != 1:
                self.main.say(self.channel, ret, MSG_MAX)
                self.logger.log(LOG_ERROR, ret)
