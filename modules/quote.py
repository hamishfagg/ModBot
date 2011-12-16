import sys
from constants import *

class Module():

    depends = ['mysql', 'logger']
    commands = {'q':        'quote',
                'quote':    'quote',
                'rq':       'randQuote',
                'randquote':'randQuote',
                'nq':       'newQuote',
                'newquote': 'newQuote'}
    hooks =    {'loaded': 'loaded'}

    def __init__(self):
        if 'twitter' in sys.modules:
            self.depends.append('twitter')
    
    def loaded(self):
        if 'twitter' not in sys.modules:
            self.logger.log(LOG_INFO, "Twitter module is not loaded.\n\t\t\t\tQuotes will not be tweeted unless the Twitter module is loaded and the Quote module is reloaded.")
        self.mysql.connect('quotes')
    
    def quote(self, user, channel, args):
        if len(args) == 0:
            quote = self.mysql.find(fields=['quote'], order="created DESC", limit=1)[0]
            self.main.msg(channel, quote[0], 10000)
        else:
            string = "%" + " ".join(args) + "%"
            quotes = self.mysql.execute("SELECT * FROM quotes WHERE UPPER(`quote`) LIKE UPPER(%s) LIMIT 6",  (string,))
            for i in range(5):
                if i == len(quotes):
                    break
                self.main.msg(channel, quotes[i][2], MSG_MAX)
            if len(quotes) > 5:
                self.main.msg(channel, "Exceeded maximum search results. Try a more specific search", MSG_MAX)

    def randQuote(self, user, channel, args):
        quote = self.mysql.find(order="rand()", limit=1)
        self.main.msg(channel, quote[0][2], MSG_MAX)

    def newQuote(self, user, channel, args):
        if user in self.main.channels[channel]['admins']:
            self.mysql.insert(data={'user': user, 'quote': " ".join(args)})
            self.main.msg(channel, "Quote was saved successfully", MSG_MAX)
            
            if 'twitter' in self.depends:
                self.twitter.tweetQuote(" ".join(args))
