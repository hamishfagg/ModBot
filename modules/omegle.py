import omeglehandler as Omegle
import time
from constants import *

class Module():
	depends = ['logger']
	hooks = {'privmsg': 'privmsg'}
	commands = {'omegle': 'cmdOmegle',
				'disconnect': 'cmdDisconnect',
				'cap': 'cmdCap',
				'kick': 'cmdKick',
				'inject': 'cmdInject'}

	clients = {}
	captcha = None

	def cmdOmegle(self, user, channel, args):
		if self.clients.get(channel, None) == None: # There's no session going on in this channel yet
			if len(args) == 0:
				self.logger.log(LOG_DEBUG, "Starting Omegle in single mode, channel %s" % channel)
				self.clients[channel] = {'mode': 'single', 'clients': [Omegle.Omegle(self, channel, 0)], 'running': True}

			elif args[0] == 'spy':
				self.logger.log(LOG_DEBUG, "Starting Omegle in spy mode, channel %s" % channel)
				self.clients[channel] = {'mode': 'spy', 'clients': [Omegle.Omegle(self, channel, 0), Omegle.Omegle(self, channel, 1)], 'running': True}

			elif args[0] == 'party':
				if len(args) > 1:
					num = int(args[1])
				else: num = 4
				self.logger.log(LOG_DEBUG, "Starting Omegle in spy mode, channel %s" % channel)
				self.clients[channel] = {'mode': 'party', 'clients':[], 'running': True, 'count': 4}
				for i in range(0, num):
					self.clients[channel]['clients'].append(Omegle.Omegle(self, channel, i))
			if self.captcha == None:
				self.clients[channel]['clients'][0].connect()
			else:
				self.main.msg(channel, "Waiting on captcha before connecting: %s" % self.captcha[2], MSG_MAX)
		

	def cmdDisconnect(self, user, channel, args): # It's easier to not wait for replies
		if channel in self.clients:
			self.clients[channel]['running'] = False
			for client in self.clients[channel]['clients']: client.disconnect()
			self.main.msg(channel, "You have disconnected.", MSG_MAX)
			time.sleep(1)
			del self.clients[channel]

	def cmdKick(self, user, channel, args):
		if channel in self.clients and len(args) > 0: # An index was given
			if len(args) > 1:
				message = "** Stranger %s is being kicked. (Reason: %s) **" % (int(args[0])-1, " ".join(args[1:]))
			else:
				message = "** Stranger %s is being kicked **" % str(int(args[0])-1)
			self.sendToAll(channel, int(args[0])-1, message)
			self.clients[channel]['clients'][int(args[0])-1].disconnect()
	
	def cmdInject(self, user, channel, args):
		if channel in self.clients and self.clients[channel]['mode'] != 'single' and len(args) > 0:
			try:
				index = int(args[0])
			except:
				index = 0

			if index == 0: # Inject to all clients
				self.sendToAll(channel, None, " ".join(args))
			else:
				self.clients[channel]['clients'][index-1].sendMsg(" ".join(args[1:]))

	def privmsg(self, user, channel, message):
		if channel in self.clients:
			if self.clients[channel]['mode'] == 'single':
				self.clients[channel]['clients'][0].sendMsg("<%s> %s" % (user, message))
	
	def cmdCap(self, user, channel, args):
		if len(args) > 0 and channel in self.clients:
			for client in self.clients[channel]['clients']:
				if not client.challenge == None:
					client.sendCaptcha(" ".join(args))
					break

	def action(self, user, channel, data):
		if channel in self.clients:
			if self.clients[channel]['mode'] == 'single':
				self.clients[channel]['clients'][0].sendMsg("* %s %s" % (user, data))	

	def sendToAll(self, channel, exclude, message):
		for client in self.clients[channel]['clients']:
			if client.index != exclude and client.index != None:
				client.sendMsg(message)

	def on_connected(self, channel, index):
		#time.sleep(5)
		if self.clients[channel]['mode'] == 'single':
			self.logger.log(LOG_INFO, "Connected to a stranger.")
			self.clients[channel]['clients'][0].sendMsg("Surprise, you're not talking to one stranger. You're actually talking to an IRC channel!")
			self.main.msg(channel, "Connected to a stranger. Say hi!", MSG_MAX)
		
		else:
			self.main.msg(channel, "Stranger %s connected." % str(index+1), MSG_MAX)
			if self.clients[channel]['mode'] == 'party':
				self.clients[channel]['clients'][index].sendMsg("Surprise! You're not talking to just one stranger, you're actually talking to %s!\nDifferent strangers are prefixed with a number so that you can tell them apart.\n- You are stranger number %s -" % (self.clients[channel]['count'], str(index+1)))
				
				self.sendToAll(channel, index, "** Stranger %s has connected **" % str(index+1))

			#connect the next client for this channel
			if self.connectNext(channel): return

		# code reaches here if there are no more unconnected clients for the current channel
		# check other channels
		for chan in self.clients:
			for client in self.clients[chan]['clients']:
				if client.index == None:
					connectNext(chan)

	def connectNext(self, channel):
		if self.captcha == None:
			for client in self.clients[channel]['clients']:
				if client.id == None:
					client.connect()
					return True
			return False
		else: return True # this makes connect() exit, and stop bothering us.
		
	def on_message(self, channel, index, message):
		if self.clients[channel]['mode'] == 'single':
			message = "Stranger: " + message
			self.logger.log(LOG_INFO, message)
			self.main.msg(channel, message.encode('ascii', 'replace'), MSG_MAX)

		else:
			if self.clients[channel]['mode'] == 'spy':
				newindex = index*(-1) + 1
				self.clients[channel]['clients'][newindex].sendMsg(message)
			else:
				print "%s: %s" % (str(index+1), message)
				self.sendToAll(channel, index, "%s: %s" % (str(index+1), message))
			self.main.msg(channel, "Stranger %s: %s" % (str(index+1), message.encode('ascii', 'replace')), MSG_MAX)
	
	def on_typing(self, channel, index):
		if self.clients[channel]['mode'] == 'spy':
			newindex = index*(-1) + 1
			self.clients[channel]['clients'][newindex].sendTyping()
	
	def on_stoppedTyping(self, channel, index):
		if self.clients[channel]['mode'] == 'spy':
			newindex = index*(-1) + 1
			self.clients[channel]['clients'][newindex].sendStoppedTyping()

	def on_recaptcha(self, channel, index, url):
		self.main.msg(channel, "Recaptcha required: %s" % url, MSG_MAX)
		self.captcha = [channel, index, url] #this is to keep track of where the captcha is needed, and to stop new clients connecting

	def on_recaptchaResponse(self, channel, index, accepted):
		if accepted == True:
			self.captcha = None
			self.main.msg(channel, 'Recaptcha accepted!', MSG_MAX)
		else: self.main.msg(channel, 'Recaptcha rejected!', MSG_MAX)

	def on_disconnected(self, channel, index, reason):
		if channel in self.clients:
			if self.clients[channel]['mode'] == 'single' and self.clients[channel]['running']:
				self.main.msg(channel, "Stranger disconnected", MSG_MAX)
				del self.clients[channel]
				
			elif self.clients[channel]['mode'] == 'spy':
				if self.clients[channel]['running']:
					self.clients[channel]['running'] = False
					self.main.msg(channel, "Stranger %s has disconnected." % str(index+1), MSG_MAX)
					if self.clients[channel]['clients'][index*(-1)+1].id != None: self.clients[channel]['clients'][index*(-1)+1].disconnect()
					self.main.msg(channel, "You have disconnected.", MSG_MAX)
					del self.clients[channel]

			else:
				if self.clients[channel]['running']:
					self.main.msg(channel, "Stranger %s has disconnected." % str(index+1), MSG_MAX)
					if self.captcha == None:
						self.sendToAll(channel, index, "** Stranger %s has disconnected. Finding a new Stranger... **" % str(index+1))
						self.connectNext(channel)
					else:
						self.sendToAll(channel, index, "** Stranger %s has disconnected. Waiting for an operator to solve captcha before connecting another stranger.. **" % str(index+1))
				
