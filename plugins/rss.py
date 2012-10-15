from constants import *
from rssconf import *
import feedparser
import threading

class Plugin():

    hooks = {'loaded': 'loaded',
        'minutetimer': 'checkFeeds'}

    def loaded(self):
        self.current = {}
        for feed in feeds: self.current[feed] = ""
        self.checkFeeds(False)

    def checkFeeds(self, say=True):
        for feed in feeds:
            self.p = feedparser.parse(feeds[feed])
            if self.p.entries[0].date != self.current[feed]:
                #Make a list of all the new entries
                new = []
                for entry in self.p.entries:
                    if entry.date == self.current[feed]: break
                    new += ["%s: %s - %s" % (feed, entry.title.encode('ascii'), entry.link.encode('ascii'))]
                new.reverse()
                if say:
                    for post in new:
                        self.main.msg(self.main.channel, post)
                self.current[feed] = self.p.entries[0].date
