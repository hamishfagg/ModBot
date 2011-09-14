import omeglehandler as Omegle
from constants import *

class Module():
	depends = ['logger']
	hooks = {'privmsg': 'privmsg'}
	commands = {'omegle': 'cmdOmegle',
				'disconnect': 'cmdDisconnect',
				'cap': 'recap'}

	clients = {}

	def cmdOmegle(self, user, channel, args):
		if self.clients.get(channel, None) == None: # There's no session going on in this channel yet
			if len(args) == 0:
				self.logger.log(LOG_DEBUG, "Starting in single mode, channel %s" % channel)
				self.clients[channel] = {'mode': 'single', 'clients': [Omegle.Omegle(self, channel, 0)]}

			elif args[0] == 'spy':
				self.logger.log(LOG_DEBUG, "Starting in spy mode, channel %s" % channel)
				self.clients[channel] = {'mode': 'spy', 'clients': [Omegle.Omegle(self, channel, 0), Omegle.Omegle(self, channel, 1)]}

			for client in self.clients[channel]['clients']: client.connect()		
		

	def cmdDisconnect(self, user, channel, args): # It's easier to not wait for replies
		if channel in self.clients:
			for client in self.clients[channel]['clients']: client.disconnect()
			self.main.msg(channel, "You have disconnected.", MSG_MAX)
			del self.clients[channel]

	def privmsg(self, user, channel, message):
		if channel in self.clients:
			if self.clients[channel]['mode'] == 'single':
				self.clients[channel]['clients'][0].sendMsg("<%s> %s" % (user, message))
	
	def recap(self, user, channel, args):
		if len(args) > 0 and channel in self.clients:
			for client in self.clients[channel]['clients']:
				if not client.challenge == None:
					client.sendCaptcha(" ".join(args))
					break

	def action(self, user, channel, data):
		if channel in self.clients:
			if self.clients[channel]['mode'] == 'single':
				self.clients[channel]['clients'][0].sendMsg("* %s %s" % (user, data))	




	def on_connected(self, channel, index):
		if self.clients[channel]['mode'] == 'single':
			self.logger.log(LOG_INFO, "Connected to a stranger.")
			self.clients[channel]['clients'][0].sendMsg("Surprise, you're not talking to one stranger. You're actually talking to an IRC channel!")
			self.main.msg(channel, "Connected to a stranger. Say hi!", MSG_MAX)
		
		else:
			self.main.msg(channel, "Stranger %s connected." % str(index+1), MSG_MAX)
		
	def on_message(self, channel, index, message):
		if self.clients[channel]['mode'] == 'single':
			message = "Stranger: " + message
			self.logger.log(LOG_INFO, message)
			self.main.msg(channel, message.encode('ascii', 'replace'), MSG_MAX)

		else:
			if self.clients[channel]['mode'] == 'spy':
				newindex = index*(-1) + 1
				self.clients[channel]['clients'][newindex].sendMsg(message)
			self.main.msg(channel, "Stranger %s: %s" % (str(index+1), message.encode('ascii', 'replace')), MSG_MAX)
	
	def on_typing(self, channel, index):
		print "%s typing" % index
		if self.clients[channel]['mode'] == 'spy':
			newindex = index*(-1) + 1
			self.clients[channel]['clients'][newindex].sendTyping()
	
	def on_stoppedTyping(self, channel, index):
		if self.clients[channel]['mode'] == 'spy':
			newindex = index*(-1) + 1
			self.clients[channel]['clients'][newindex].sendStoppedTyping()

	def on_recaptcha(self, channel, index, url):
		self.main.msg(channel, "Recaptcha required: %s" % url, MSG_MAX)

	def on_recaptchaResponse(self, channel, index, accepted):
		if accepted == True: self.main.msg(channel, 'Recaptcha accepted!', MSG_MAX)
		else: self.main.msg(channel, 'Recaptcha rejected!', MSG_MAX)

	def on_disconnected(self, channel, index, reason):
		if channel in self.clients:
			if self.clients[channel]['mode'] == 'single':
				self.main.msg(channel, "Stranger disconnected", MSG_MAX)
				del self.clients[channel]
				
			elif self.clients[channel]['mode'] == 'spy':
				self.main.msg(channel, "Stranger %s has disconnected." % str(index+1), MSG_MAX)
				self.clients[channel]['clients'][index*(-1)+1].disconnect()
				self.main.msg(channel, "You have disconnected.", MSG_MAX)
				del self.clients[channel]
