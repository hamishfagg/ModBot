import sys
from constants import *

class Module():

    depends = ['mysql', 'logger']
    commands = {'q': 'quote',
                'quote': 'quote',
                'rq': 'randQuote',
                'randquote':'randQuote',
                'nq': 'newQuote',
                'newquote': 'newQuote'}
    hooks = {'loaded': 'loaded'}


    def __init__(self, main, channel):
        if 'twitter' in main.channels[channel].modules:
            self.depends.append('twitter')
    
    def loaded(self):
        try: getattr(self, 'twitter')
        except: self.logger.log(LOG_INFO, "Twitter module is not loaded.\n\t\t\t\tQuotes will not be tweeted unless the Twitter module is loaded and the Quote module is reloaded.")
        self.tableName = 'quotes'
        self.mysql.connect()

    def moduleloaded(self, module):
        if module == "twitter":
            self.depends.append('twitter')
            self.twitter = self.main.channels[self.channel]['modules']['twitter']['module']

    def quote(self, user, channel, args, PM):
        if len(args) == 0:
            quote = self.mysql.find(self.tableName, fields=['quote'], conditions={'channel': self.channel}, order="created DESC", limit=1)[0]
            self.main.msg(channel, quote[0], 10000)
        else:
            print self.channel
            string = "%" + " ".join(args) + "%"
            quotes = self.mysql.execute("SELECT * FROM "+self.tableName+" WHERE UPPER(`quote`) LIKE UPPER(%s) AND `channel` = %s LIMIT 6", (string, self.channel))
            for i in range(5):
                if i == len(quotes):
                    break
                self.main.msg(channel, quotes[i][2], MSG_MAX)
            if len(quotes) > 5:
                self.main.msg(channel, "Exceeded maximum search results. Try a more specific search", MSG_MAX)

    def randQuote(self, user, channel, args, PM):
        quote = self.mysql.find(self.tableName, order="rand()", limit=1)
        self.main.msg(channel, quote[0][2], MSG_MAX)

    def newQuote(self, user, channel, args, PM):
        if user in self.main.channels[channel]['admins']:
            self.mysql.insert(self.tableName, data={'user': user, 'quote': " ".join(args), 'channel':self.channel})
            self.main.msg(channel, "Quote was saved successfully", MSG_MAX)
            
            if 'twitter' in self.depends:
                self.twitter.tweetQuote(" ".join(args))
