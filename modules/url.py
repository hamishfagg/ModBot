from constants import *
import subprocess
from BeautifulSoup import BeautifulSoup

class Module():

	commands = {'shorten': 'shorten'}
	depends = ['logger']
	hooks = {'privmsg': 'privmsg'}

	def shorten(self, user, channel, args):
		if args:
			self.logger.log(LOG_DEBUG, "Shortening '%s'" % args[0])
			self.main.msg(channel, self.getShortUrl(args[0]), MSG_MAX)

	def getShortUrl(self, url):
		cmd = 'curl https://www.googleapis.com/urlshortener/v1/url -H "Content-Type: application/json" -d \'%s\'' % '{"longUrl": "%s"}' % url
		output, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		return output[output.index('"id"'):].split('"')[3]

	def privmsg(self, user, channel, message):
		if user != channel:
			args = message.split()
			for arg in args:
				if arg.startswith("http://") or arg.startswith("https://"): #this argument is a URL
					output, err = subprocess.Popen("curl -L " + arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
					soup = BeautifulSoup(output)
					
					self.main.msg(channel, soup.html.head.title.string.strip().encode('ascii').replace("\n", " "), MSG_MAX)
