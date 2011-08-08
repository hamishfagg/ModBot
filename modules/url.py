from constants import *
import subprocess

class Module():

	commands = {'shorten': 'shorten'}

	def shorten(self, user, channel, args):
		self.main.msg(channel, self.getShortUrl(args[0]), MSG_MAX)

	def getShortUrl(self, url):
		cmd = 'curl https://www.googleapis.com/urlshortener/v1/url -H "Content-Type: application/json" -d \'%s\'' % '{"longUrl": "%s"}' % url
		output, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		return output[output.index('"id"'):].split('"')[3]
