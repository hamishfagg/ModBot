from constants import *

class Module():

    commands = {'say': 'say'}

    def say(self, user, channel, args):
        if self.main.users[user].isAdmin(channel):
            self.main.msg(self.channel, " ".join(args))
