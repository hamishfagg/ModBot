from constants import *
from rssconf import *
import feedparser
import threading

class Module():

    hooks = {'loaded': 'loaded',
        'minutetimer': 'checkFeeds'}

    def loaded(self):
        self.current = {}
        for feed in feeds: self.current[feed] = ""
        self.checkFeeds(False)

    def checkFeeds(self, say=True):
        for feed in feeds:
            p = feedparser.parse(feeds[feed])
            if p.entries[0].date != self.current[feed]:
                #Make a list of all the new entries
                new = []
                for entry in p.entries:
                    if entry.date == self.current[feed]: break
                    new += ["%s: %s - %s" % (feed, entry.title.encode('ascii'), entry.link.encode('ascii'))]
                new.reverse()
                for post in new:
                    if say: self.main.msg(self.channel, post, MSG_MAX)
                self.current[feed] = p.entries[0].date
