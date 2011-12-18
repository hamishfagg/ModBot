# todo: sync all channels
from constants import *
class Module():
    
    commands = {'away': 'away'}
    hooks = {'privmsg' : 'privmsg',
             'userleft': 'userleft'}

    def __init__(self):
        self.reasons = {}

    def away(self, user, channel, args):
        reason = " ".join(args)
        if len(reason) == 0:
                reason = 'None'
        if self.reasons.get(user.lower(), None) == None:
            self.reasons[user.lower()] = {'reason': reason, 'mentions': []}
            self.main.say(channel, "%s%s is now away. Reason: %s." % (COLOUR_DEFAULT, user, reason), MSG_MAX)
        else:
            if len(self.reasons[user.lower()]['mentions']) > 0:
                self.main.msg(user, 'You were called for %s times while you were gone:' % len(self.reasons[user.lower()]['mentions']), MSG_MAX)
                for line in self.reasons[user.lower()]['mentions']:
                    self.main.msg(user, line, MSG_MAX)
            del self.reasons[user.lower()]
            self.main.say(channel, "%s%s is no longer away." % (COLOUR_DEFAULT, user), MSG_MAX)

    def userleft(self, user, channel):
        print 'userleft'
        if self.reasons.get(user.lower(), None) != None:
            del self.reasons[user.lower()]

    def privmsg(self, user, channel, message):
        words = message.split(' ', 1)

        if self.reasons.get(user.lower(), None) != None and not message.startswith('!away'):
            self.main.notice(user, 'You are currently set as away.')

        elif (words[0].endswith(':') or words[0].endswith(',')) and self.reasons.get(words[0][:-1].lower(), None) != None:
            self.main.say(channel, "%s%s is currently away. Reason: %s" % (COLOUR_DEFAULT, words[0][:-1], self.reasons.get(words[0][:-1].lower())['reason']), MSG_MAX)
            self.reasons[words[0][:-1].lower()]['mentions'].append('<%s> %s' % (user, message))
