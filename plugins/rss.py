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
                print "new stuff"
                for entry in self.p.entries:
                    if entry.date == self.current[feed]: break
                    print "new"
                    new += ["%s: %s - %s" % (feed, entry.title.encode('ascii'), entry.link.encode('ascii'))]
                new.reverse()
                for post in new:
                    if say: self.main.msg(self.main.channel, post)
                self.current[feed] = self.p.entries[0].date
