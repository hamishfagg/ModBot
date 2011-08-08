from constants import *
import subprocess

class Module():

	commands = {'shorten': 'shorten'}

	def shorten(self, user, channel, args):
		cmd = 'curl https://www.googleapis.com/urlshortener/v1/url -H "Content-Type: application/json" -d \'%s\'' % '{"longUrl": "%s"}' % args[0]
		output, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		url = output[output.index('"id"'):].split('"')[3]
		self.main.msg(channel, url, MSG_MAX)
