from constants import *
from datetime import datetime

class Module():

### NOTE: Polls are currently bot-wide. There is no separate poll per channel.

    depends = ['logger', 'mysql']
    hooks = {'loaded': 'loaded'}
    commands = {'closepoll': 'closePoll',
                'poll': 'poll',
                'newpoll': 'newPoll',
                'vote': 'vote'}

    def loaded(self):
        self.tableName = 'polls'
        self.mysql.connect()
        self.updateCurrent()
    
    def updateCurrent(self):
        self.current = self.mysql.execute("SELECT * FROM polls WHERE `closed` = 0 AND `channel` = %s LIMIT 1", self.channel)
        if len(self.current) == 0: self.current = None
        else: self.current = self.current[0]

    def poll(self, user, channel, args):
        args = args[1:]
        if self.current == None:
            self.main.msg(channel, "There is currently no poll.")
        elif user in self.main.users:
            self.main.msg(channel, "The current poll is: %s" % self.current[2])
            self.main.msg(channel, "Current votes:%s %s%s /%s %s%s." % (COLOUR_GREEN, str(self.current[3]), COLOUR_DEFAULT, COLOUR_RED, str(self.current[4]), COLOUR_DEFAULT))
            self.main.msg(channel, "Type '!vote yes' or '!vote no' to vote.")

    def closePoll(self, user, channel, args):
        args = args[1:]
        self.mysql.update(self.tableName, data={'closed': datetime.now()}, conditions={'id': self.current[0]})
        if self.current != None:
            for chan in self.main.channels:
                self.main.msg(chan, "The poll has been closed!")
                self.main.msg(chan, self.current[2])
                self.main.msg(chan, "Results:%s %s%s votes to%s %s%s." % (COLOUR_GREEN, str(self.current[3]), COLOUR_DEFAULT, COLOUR_RED, str(self.current[4]), COLOUR_DEFAULT))
            self.current = None
        else:
            if PM: channel = user
            self.main.msg(channel, "There is currently no poll.")

    def newPoll(self, user, channel, args):
        args = args[1:]
        poll = " ".join(args)
        if user in self.main.channels[channel]['admins']:
            if len(poll) != 0:
                if self.current != None: self.closePoll(user, channel, None, None)
                self.mysql.insert(self.tableName, data={'user': user, 'poll': poll, 'channel': self.channel})
                self.updateCurrent()
                for channel in self.main.channels:
                    self.main.msg(channel, "There is a new poll: %s" % self.current[2])
                    self.main.msg(channel, "Type '!vote yes' or '!vote no' to vote.")

    def vote(self, user, channel, args):
        args = args[1:]
        if PM: channel = user
        if self.current == None:
            self.main.msg(channel, "There is currently no poll.")
        elif len(self.mysql.find(table='votes', conditions={'user': user, 'poll_id': self.current[0]}, limit=1)) != 0:
            self.main.msg(channel, "You have already voted on this poll.")
        elif args[0].lower() == 'yes' or args[0].lower() == 'no':
            if args[0].lower() == 'yes':
                votetype = 'yes'
                num = self.current[3] + 1
                vote = 1
            else:
                votetype = 'no'
                num = self.current[4] + 1
                vote = 0

            self.mysql.update(self.tableName, data={votetype: num}, conditions={'id': self.current[0]})
            self.mysql.insert(table='votes', data={'poll_id': str(self.current[0]), 'user': user, 'host': self.main.host, 'vote': vote})
            self.updateCurrent()
            self.main.msg(channel, "Your vote has been cast.")
