import sys
sys.path.append("modules")
from constants import *
import log
import threading
import time
import traceback
from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc
#from startup import *

MSGHACK = 100000

class Bot(irc.IRCClient):

	nickname = sys.argv[2]

	## Instance init.
	def __init__(self):
		self.logger = log.Module()
		self.admins = []
		self.users = []
		self.modules = dict()
		self.colour = chr(3) + '14'
		self.startupErr = {}
		self.inchannel = False
		self.connected = False
		#for mod in startup:
		#	self.loadModule(mod, None)
	

	""" ADMIN LIST HANDLING """
	
	## List users in 'channel'. Used for gaining user modes on join.
	# @param channel The channel for which to list names.
	def who(self, channel):
		self.logger.log(LOG_DEBUG, "Retreiving user list.")
		self.sendLine('WHO %s' % channel)

	## Recieve a WHO reply from the server.
	# @param nargs A list of arguments including modes etc. See twisted documentation for details.
	def irc_RPL_WHOREPLY(self, *nargs):
		if nargs[1][6].endswith('~') or nargs[1][6].endswith('&') or nargs[1][6].endswith('@'):
       			self.admins.append(nargs[1][5])
		self.users.append(nargs[1][5])

	## Called when WHO output is complete.
	# @param nargs A list of arguments including modes etc. See twisted documentation for details.
	def irc_RPL_ENDOFWHO(self, *nargs):
		#This is to stop the hook being run before user lists are populated
		self.logger.log(LOG_INFO, "Found admins: " + " ".join(self.admins))
		self.runHook("joined", self.factory.channel)
		
		
	## Runs a given function in all loaded modules. Handles any resulting errors.
	# @param hook The name of the hook to be run. This is a name of a function in the irc.IRCClient class and also the name of the method from which this one will be called in this case.
	# @param args A list of the arguments to be passed to the hook function.
	def runHook(self, hook, *args):
		self.logger.log(LOG_DEBUG, "Running hook %s" % hook)
		for module in self.modules:
			functionName = self.modules[module]['hooks'].get(hook, None)
			if functionName != None:
				try:
					function = getattr(self.modules[module]['module'], functionName)
					function(*args)
				except Exception,e:
					self.say(self.factory.channel, "Error running %s hook in module %s: %s" % (hook, module, str(sys.exc_info()[1])), MSGHACK)
					self.logger.log(LOG_ERROR, "Error running %s hook in module %s\n%s\n" % (hook, module, "".join(traceback.format_tb(sys.exc_info()[2]))))

	def runCmd(self, cmd, *args):
		self.logger.log(LOG_DEBUG, "Running cmd %s" % cmd)
		for module in self.modules:
			functionName = self.modules[module]['commands'].get(cmd, None)
			if functionName != None:
				try:
					function = getattr(self.modules[module]['module'], functionName)					
					function(*args)
				except Exception,e:
					self.say(self.factory.channel, "Error running %s command in module %s: %s" % (cmd, module, str(sys.exc_info()[1])), MSGHACK)
					self.logger.log(LOG_ERROR, "Error running %s command in module %s\n%s\n" % (cmd, module, "".join(traceback.format_tb(sys.exc_info()[2]))))
	
	## Tries to load a given module name and handles any errors. If the module is already loaded, it uses 'reload' to reload the module.
	# @param moduleName The name of the module that should be looked for.
	# @param channel The channel to send a loaded/failed message to. Allows load commands sent in PM to be replied to in PM.
	def loadModule(self, moduleName, channel):
		self.logger.log(LOG_DEBUG, "Attempting to load '%s'" % moduleName)
		try:
			if moduleName in sys.modules:
				self.logger.log(LOG_DEBUG, "%s is in sys.modules - reloading" % moduleName)
				#module = reload(sys.modules[moduleName])
			else:
				module = __import__(moduleName)
				module = module.Module() 		#Get an object containing the 'Module' class of the given module
				module.main = self

				# Check dependancies
				if hasattr(module, 'depends'):
					for depend in module.depends:
						if depend in sys.modules:
							self.logger.log(LOG_DEBUG, " - Dependancy '%s' is loaded" % depend)
							setattr(module, depend, sys.modules[depend].Module())
						else:
							self.logger.log(LOG_ERROR, "Failed to load %s: A dependancy (%s) is not loaded." % (moduleName, depend))
							self.msg(channel, "Couldn't load module \'%s\': A dependancy (%s) is not loaded." % (moduleName, depend), MSGHACK)
							return
				else:
					self.logger.log(LOG_DEBUG, "No dependancies found.")
			
			self.modules[moduleName] = {'module': module}
			self.modules[moduleName]['hooks'] = getattr(module, 'hooks', {})
			self.modules[moduleName]['commands'] = getattr(module, 'commands', {})
			
			self.logger.log(LOG_INFO, "Module '%s' has been loaded." % moduleName)

			if self.inchannel: #Stop calls to 'msg' when startup modules are loaded
				self.msg(channel, "%sLoaded module \'%s\'." % (self.colour, moduleName), MSGHACK)
			self.runHook('loaded')

		except:
			raise
			if self.inchannel: self.msg(channel, "Couldn't load module \'%s\': %s" % (moduleName, str(sys.exc_info()[1])), MSGHACK)
			else: self.startupErr[moduleName] = sys.exc_info()[1]
			self.logger.log(LOG_ERROR, "Error loading module '%s':\n%s" % (moduleName, "".join(traceback.format_tb(sys.exc_info()[2]))))

	""" TWISTED HOOKS """

	## Called when the bot recieves a notice.
	# @param user The user that the notice came from.
	# @param channel The channel that the notice was sent to. Will be the bot's username if the notice was sent to the bot directly and not to a channel
	def noticed(self, user, channel, message):
		print 'NOTICE: <%s> %s' % (user, message)
		self.runHook("noticed", user, channel, message)

	## Called when the bot signs on to a server.
	def signedOn(self):
		self.connected = True
		self.runHook("signedOn")
		self.join(self.factory.channel)
		if len(sys.argv) > 3:
			self.msg('nickserv', "identify %s" % sys.argv[3], MSGHACK)
		self.keepAlive()

	## Called when the bot joins a channel.
	# @param channel The channel that the bot has joined.
	def joined(self, channel):
		self.inchannel = True
		
		#Report startup errors
		if len(self.startupErr) != 0:
			self.say(self.factory.channel, "Errors occured loading modules on startup:", MSGHACK)
			for moduleName in self.startupErr:
				self.say(self.factory.channel, "Couldn't load module \'%s\': %s" % (moduleName, self.startupErr[moduleName]), MSGHACK)
				

		#Build list of admins in the channel
		self.who(self.factory.channel)
	
	## Called when the bot leaves a channel
	# @param channel The channel that the bot has left.
	def left(self, channel):
		print "LEFT CHANNEL"
		self.runHook("left", channel)

	## Called when a user leaves a channel that the bot is in.
	# @param user The user that has left 'channel'.
	# @param channel The channel that 'user' has left.
	def userLeft(self, user, channel):
		user = user.split('!', 1)[0]
		print 'User %s has left' % user
		if user in self.admins:
			self.admins.remove(user)
		self.users.remove(user)
		self.runHook("userLeft", user, channel)

	## Called when the bot sees a user disconnect.
	# @param user The user that has quit.
	# @param quitMessage The message that the user gave for quitting.
	def userQuit(self, user, quitMessage):
		user = user.split('!', 1)[0]
		print 'User %s has quit' % user
		if user in self.admins:
			self.admins.remove(user)
		self.users.remove(user)
		self.runHook("userQuit", user, quitMessage)

	## Called when the bot sees a user join a channel that it is in.
	# @param user The user that has joined.
	# @param channel The channel that the user has joined.
	def userJoined(self, user, channel):
		user = user.split('!', 1)[0]
		print 'User %s has joined' % user
		self.users.append(user)
		self.runHook("userJoined", user, channel)

	## Called when the bot recieves a message from a user or channel.
	# @param user The user that the message is from.
	# @param channel The channel that the message was sent to. Will be te bot's username if the message was a private message.
	# @param message The message, derp.
	def privmsg(self, user, channel, message):
		userinfo = user.split('!', 1)
		user = userinfo[0]
		if channel == self.username: print 'PM: <%s> %s' % (user, message)
		else: print '<%s> %s' % (user, message)
		if channel == self.username: msgchannel = user
		else: msgchannel = channel
		self.host = userinfo[1].lower()
		words = message.split()
		if words[0].startswith('!'):
			self.runCmd(words[0][1:], user, channel, words[1:])
		if user in self.admins:
			if words[0] == '!load':
				for mod in words[1:]:
					self.loadModule(mod, msgchannel)
			if words[0] == '!unload':
				for mod in words[1:]:
					if self.modules.get(mod, None) == None:
						self.msg(msgchannel, "Module \'%s\' wasn\'t loaded." % mod, MSGHACK)
					else:
						del self.modules[mod]
						self.msg(msgchannel, "Module \'%s\' unloaded." % mod, MSGHACK)
		self.runHook("privmsg", user, channel, message)
	
	## Called when users or channel's modes are changed.
	# @param user The user who instigated the change.
	# @param channel The channel where the modes are changed. If args is empty the channel for which the modes are changing. If the changes are at server level it could be equal to 'user'.
	# @param set True if the mode(s) is being added, False if it is being removed.
	# @param modes The mode or modes which are being changed.
	# @param args Any additional information required for the mode change.
	def modeChanged(self, user, channel, set, modes, args):
		if (channel == self.factory.channel) and (modes.startswith('q') or modes.startswith('a') or modes.startswith('o')):
			if set:
				for username in args:
					if not username in self.admins:
						self.admins.append(username)
			else:
				for username in args:
					self.admins.remove(username)
		self.runHook("modeChanged", user, channel, set, modes, args)

	## A function to check the liveness of the socket. This is MEANT to be implemented in twisted.
	def keepAlive(self):
		def f():
			while self.connected:
				self.ping("irc.rizon.net")
				time.sleep(10)
		
		def start_thread():
			thread = threading.Thread(target=f)
			thread.daemon = True
			thread.start()
		
		start_thread()
			

	""""""

class BotFactory(protocol.ClientFactory):
	protocol = Bot

	def __init__(self, channel, nickname=None):
		self.channel = channel
		self.nickname = nickname

	def clientConnectionLost(self, connector, reason):
		print "Lost connection (%s), reconnecting." % (reason,)
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print "Could not connect: %s" % (reason,)

if __name__ == "__main__":
	chan = sys.argv[1]
	reactor.connectSSL('irc.rizon.net', 9999, BotFactory('#' + chan), ssl.ClientContextFactory())
	reactor.run()
