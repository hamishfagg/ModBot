import sys
from constants import *

class Plugin():

    depends = ['mysql', 'logger']
    commands = {'q': 'quote',
                'quote': 'quote',
                'rq': 'randQuote',
                'randquote':'randQuote',
                'nq': 'newQuote',
                'newquote': 'newQuote'}
    hooks = {'loaded': 'loaded'}


    def loaded(self):
        if 'twitter' in self.main.plugins:
            self.twitter = self.main.plugins['twitter']
        else:
            self.logger.log(LOG_INFO, "Twitter plugin is not loaded.\n\t\t\t\tQuotes will not be tweeted unless the Twitter plugin is loaded.")
        self.tableName = 'quotes'
        self.mysql.connect()

    def moduleloaded(self, module):
        if module == "twitter":
            self.twitter = self.main.plugins['twitter']

    def quote(self, user, args):
        if len(args) == 0:
            quote = self.mysql.find(self.tableName, fields=['quote'], conditions={'channel': self.main.channel}, order="created DESC", limit=1)[0]
            self.main.msg(self.main.channel, quote[0])
        else:
            string = "%" + " ".join(args) + "%"
            quotes = self.mysql.execute("SELECT * FROM "+self.tableName+" WHERE UPPER(`quote`) LIKE UPPER(%s) AND `channel` = %s LIMIT 6", (string, self.main.channel))
            for i in range(5):
                if i == len(quotes):
                    break
                self.main.msg(self.main.channel, quotes[i][2])
            if len(quotes) > 5:
                self.main.msg(self.main.channel, "Exceeded maximum search results. Try a more specific search")

    def randQuote(self, user, args):
        quote = self.mysql.find(self.tableName, order="rand()", limit=1)
        self.main.msg(self.main.channel, quote[0][2])

    def newQuote(self, user, args):
        if user in self.main.admins:
            self.mysql.insert(self.tableName, data={'user': user, 'quote': " ".join(args), 'channel':self.main.channel})
            self.main.msg(self.main.channel, "Quote was saved successfully")
            
            if hasattr(self, 'twitter'):
                self.twitter.tweetQuote(" ".join(args))
