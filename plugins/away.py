from constants import *
class Plugin():
    
    commands = {'away': 'away'}
    hooks = {'privmsg' : 'privmsg',
             'userleft': 'userleft',
             'userquit': 'userleft'}

    def __init__(self):
        self.reasons = {}

    def away(self, user, args):
        reason = " ".join(args[1:])
        if len(reason) == 0:
                reason = 'None'
        if self.reasons.get(user.lower(), None) == None:
            self.reasons[user.lower()] = {'reason': reason, 'mentions': []}
            self.main.msg(self.main.channel, "%s%s is now away. Reason: %s." % (COLOUR_BOLD, user, reason))
        else:
            if len(self.reasons[user.lower()]['mentions']) > 0:
                self.main.msg(user, 'You were called for %s times while you were gone:' % len(self.reasons[user.lower()]['mentions']))
                for line in self.reasons[user.lower()]['mentions']:
                    self.main.msg(user, line)
            del self.reasons[user.lower()]
            self.main.msg(self.main.channel, "%s%s is no longer away." % (COLOUR_BOLD, user))

    def userleft(self, user, channel=None):
        if self.reasons.get(user.lower(), None) != None:
            del self.reasons[user.lower()]

    def privmsg(self, user, channel, message):
        words = message.split(' ', 1)
        user = user.split('!', 1)[0]

        if self.reasons.get(user.lower(), None) != None and not message.startswith('!away'):
            self.main.notice(user, 'You are currently set as away.')

        elif (words[0].endswith(':') or words[0].endswith(',')) and self.reasons.get(words[0][:-1].lower(), None) != None:
            self.main.msg(self.main.channel, "%s is currently away. Reason: %s" % (words[0][:-1], self.reasons.get(words[0][:-1].lower())['reason']))
            self.reasons[words[0][:-1].lower()]['mentions'].append('<%s> %s' % (user, message))
