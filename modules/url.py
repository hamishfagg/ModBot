from modulecommon import *
import subprocess

class Module(irc.IRCClient):
	def __init__(self, main):
		self.main = main

	def privmsg(self, user, channel, message):
		words = message.split(' ', 1)
		if channel == self.main.username: channel = user.split('!', 1)[0]
		
		if words[0] == '!shorten':
			cmd = 'curl https://www.googleapis.com/urlshortener/v1/url -H "Content-Type: application/json" -d \'%s\'' % '{"longUrl": "%s"}' % words[1].split(' ', 1)[0]
			output, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
			url = output[output.index('"id"'):].split('"')[3]
			self.main.msg(channel, url, MSGHACK)
