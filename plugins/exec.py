"""
###### WARNING ######

This module allows you to execute python code directly from IRC.
While it is useful for debugging and only able to be used by admins, it is still VERY dangerous.

So, it's not loaded by default and I would STRONGLY ADVISE AGAINST DOING THAT. Only load it when you need it.

#####################
"""


from constants import *

class Plugin():
    commands = {'exec': 'execute'}
    depends = ['logger']

    def execute(self, user, args):
        if user in self.main.admins:
            cmd = " ".join(args)
            self.logger.log(LOG_WARNING, "%s is executing: %s" % (user, cmd))
            exec cmd

    def say(self, msg):
        self.main.msg(self.main.channel, msg)
