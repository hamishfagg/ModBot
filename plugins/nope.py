from constants import *

class Plugin():
    hooks = {'privmsg': 'privmsg'}

    def privmsg(self, user, channel, msg):
        if msg.startswith('!'):
            msg = msg[1:]

        if msg.lower().startswith('nope.avi'):
            self.main.say(channel, 'http://www.youtube.com/watch?v=gvdf5n-zI14')
        elif msg.lower().startswith('brilliant!'):
            self.main.say(channel, 'http://www.youtube.com/watch?v=NBh895KdXAU')
            
