from constants import *

class Module():
    depends = ['logger', 'mysql']
    hooks = {'loaded': 'loaded',
             'privmsg': 'privmsg',
             'action': 'action'}
    commands = {'stats': 'cmdStats'}

    def loaded(self):
        self.mysql.connect('stats')
        for chan in self.main.channels:
            self.channels[chan] = {}
            self.update(chan)

    def update(self, channel):
        results = self.mysql.find(table='stats', conditions={'channel': 'channel', 'stat': 'lines'})
        print results
    
    def privmsg(self, user, channel, msg):
        pass# save len(msg.split())


