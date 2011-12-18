from constants import *

class Module():

    commands = {'say': 'say'}

    def say(self, user, channel, args):
        if channel == user:
            if user in self.main.channels[self.channel]['admins']:
                self.main.msg(self.channel, " ".join(args[1:]), MSG_MAX)
