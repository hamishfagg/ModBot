from constants import *
import subprocess
import simplejson
from BeautifulSoup import BeautifulSoup

class Plugin():

    commands = {'shorten': 'shorten'}
    depends = ['logger']
    hooks = {'privmsg': 'privmsg'}

    ytBarLength = 20

    def shorten(self, user, args):
        if args:
            self.logger.log(LOG_DEBUG, "Shortening '%s'" % args[0])
            self.main.msg(self.main.channel, self.getShortUrl(args[0]))

    def getShortUrl(self, url):
        cmd = 'curl https://www.googleapis.com/urlshortener/v1/url -H "Content-Type: application/json" -d \'%s\'' % '{"longUrl": "%s"}' % url
        output, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return output[output.index('"id"'):].split('"')[3]

    def privmsg(self, user, channel, message):
        args = message.split()
        for arg in args:
            if arg.startswith("http://") or arg.startswith("https://"): #this argument is a URL
                self.logger.log(LOG_DEBUG, "Getting http data for %s" % arg)

                output, err = subprocess.Popen('curl -L "%s"' % arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                self.logger.log(LOG_DEBUG, "Done. Looking for title or youtube data..")
                try:
                    soup = BeautifulSoup(output)
                    if hasattr(soup, "html") and hasattr(soup.html, "head") and hasattr(soup.html.head, "title"):
                        self.main.msg(self.main.channel, self.htmlEncode(soup.html.head.title.string.strip()).replace("\n", " "))
                    if arg[7:19].lower().find("youtube") and arg.lower().find("watch?"):
                        vindex = arg.find("v=")
                        if not vindex == -1:
                            end = arg.find("&", vindex)
                            if end == -1: end = len(arg)
                            id = arg[vindex+2:end]
                            self.printYoutubeDetails(channel, id)
                except: pass # Failing silently isn't much of a big deal here

    def printYoutubeDetails(self, channel, id):
        url = 'curl -L "http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=jsonc&prettyprint=true"' % id
        output, err = subprocess.Popen(url, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if output.startswith("{"): #It was probably a valid video id
            details = simplejson.loads(output)

            likes = int(details['data']['likeCount'])
            dislikes = int(details['data']['ratingCount'])-int(details['data']['likeCount'])

            space = " "
            likeLength = int(likes/(dislikes*100.0)*self.ytBarLength)
            rating = "%sRating:%s %s%s%s%s%s" % (COLOUR_BOLD, COLOUR_DEFAULT, COLOUR_BLACK+",9", space*(likeLength), COLOUR_BLACK+",4", space*(self.ytBarLength-likeLength), COLOUR_DEFAULT)
            rating += "   ||  %s Views: %s%s" % (COLOUR_BOLD, COLOUR_DEFAULT, details['data']['viewCount'])
            rating += "   ||  %s Duration: %s%s" % (COLOUR_BOLD, COLOUR_DEFAULT, self.expandTime(details['data']['duration']))
            self.main.msg(self.main.channel, rating.encode('ascii', 'replace'))


    def htmlEncode(self, html):
        return html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'").replace('&laquo;', '').replace('&raquo;', '').encode('ascii', errors='ignore')

    def expandTime(self, time):
        secs = time%60
        mins = time%3600/60
        hours = time/3600

        ret = ""
        if hours != 0:
            ret = "%d:%0*d:%0*d" % (hours, 2, mins, 2, secs)
        elif mins != 0:
            ret = "%d:%0*d" % (mins, 2, secs)
        else:
            ret = "0:%0*d" % (2, secs)

        return ret
