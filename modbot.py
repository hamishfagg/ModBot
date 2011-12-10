import sys
import getpass

sys.path.append("modules")
from constants import *
import ConfigParser
from startup import *
import logger

import threading
import time
import traceback

from twisted.internet import ssl, reactor, protocol
from twisted.words.protocols import irc

nick = ''
port = 0
network = ''
usessl = False
channels = []

class Bot(irc.IRCClient):

    ## Instance init.
    def __init__(self):
        self.logger = logger.Module()
        
        self.channels = {}
        self.modules = {}
        self.startupErr = {}

        self.inchannel = False
        self.connected = False
        self.nickname = nick
        for mod in startup:
            self.loadModule(mod, None)
    

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
                self.channels[self.joining]['admins'].append(nargs[1][5])
        self.channels[self.joining]['users'].append(nargs[1][5])
        self.runHook("irc_rpl_whoreply", *nargs)

    ## Called when WHO output is complete.
    # @param nargs A list of arguments including modes etc. See twisted documentation for details.
    def irc_RPL_ENDOFWHO(self, *nargs):
        self.logger.log(LOG_INFO, "Finished Joining %s.\n\t\t\t\tFound users: %s.\n\t\t\t\tFound admins: %s" % (self.joining, ", ".join(self.channels[self.joining]['users']), ", ".join(self.channels[self.joining]['admins'])))
        self.runHook("joined", self.joining) #This is to stop the hook being run before user lists are populated
        self.runHook("irc_rpl_endofwho", *nargs)

        global channels
        channels.remove(self.joining)
        if len(channels) != 0:
            self.joining = channels[0]
            self.join(self.joining)
        else: del self.joining

    def topicUpdated(self, user, channel, newTopic):
        self.runHook("topicupdated", user, channel, newTopic)
        
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
                    # Print the error to a channel if the hook came from a specific one
                    for arg in args:
                        try:
                            if arg in self.channels:
                                self.say(arg, "Error running %s hook in module %s: %s" % (hook, module, str(sys.exc_info()[1])), MSG_MAX)
                        except:
                            pass
                    self.logger.log(LOG_ERROR, "Error running %s hook in module %s\n%s\n%s\n" % (hook, module, "".join(traceback.format_tb(sys.exc_info()[2])), str(sys.exc_info()[1])))

    def runCmd(self, cmd, *args):
        self.logger.log(LOG_DEBUG, "Running cmd %s" % cmd)
        for module in self.modules:
            functionName = self.modules[module]['commands'].get(cmd, None)
            if functionName != None:
                try:
                    function = getattr(self.modules[module]['module'], functionName)                    
                    function(*args)
                except Exception,e:
                    # Print the error to whatever channel the command came from
                    self.say(args[1], "Error running %s command in module %s: %s" % (cmd, module, str(sys.exc_info()[1])), MSG_MAX)
                    self.logger.log(LOG_ERROR, "Error running %s command in module %s\n%s\n%s\n%s\n%s\n" % (cmd, module, "".join(traceback.format_tb(sys.exc_info()[2])), sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
    
    ## Tries to load a given module name and handles any errors. If the module is already loaded, it uses 'reload' to reload the module.
    # @param moduleName The name of the module that should be looked for.
    # @param channel The channel to send a loaded/failed message to. Allows load commands sent in PM to be replied to in PM.
    def loadModule(self, moduleName, channel):
        self.logger.log(LOG_DEBUG, "Attempting to load '%s' on %s" % (moduleName, channel))
        try:
            if moduleName in sys.modules:
                self.logger.log(LOG_DEBUG, "%s is in sys.modules - reloading" % moduleName)
                module = reload(sys.modules[moduleName])
            else:
                module = __import__(moduleName)
            module = module.Module()        #Get an object containing the 'Module' class of the given module
            module.main = self

            # Check dependancies
            if hasattr(module, 'depends'):
                for depend in module.depends:
                    if depend in sys.modules:
                        self.logger.log(LOG_DEBUG, " - Dependancy '%s' is loaded" % depend)
                        setattr(module, depend, sys.modules[depend].Module())
                    else:
                        self.logger.log(LOG_ERROR, "Failed to load %s: A dependancy (%s) is not loaded." % (moduleName, depend))
                        self.msg(channel, "Couldn't load module \'%s\': A dependancy (%s) is not loaded." % (moduleName, depend), MSG_MAX)
                        return
            else:
                self.logger.log(LOG_DEBUG, "No dependancies found.")
            
            self.channels[channel]['modules'][moduleName] = {'module': module}
            self.channels[channel]['modules'][moduleName]['hooks'] = getattr(module, 'hooks', {})
            self.channels[channel]['modules'][moduleName]['commands'] = getattr(module, 'commands', {})
            
            self.logger.log(LOG_INFO, "Module '%s' has been loaded on %s." % (moduleName, channel))
            
            if self.inchannel: #Stop calls to 'msg' when startup modules are loaded
                self.msg(channel, "%sLoaded module \'%s\'." % (COLOUR_GREY, moduleName), MSG_MAX)
            if hasattr(module, 'loaded'):
                module.loaded()
            self.runHook("moduleloaded", moduleName)

        except:
            if self.channels[channel]['modules'].get(moduleName, None) != None: del self.channels[channel]['modules'][moduleName]
            if sys.modules.get(moduleName, None) != None: del sys.modules[moduleName]

            raise
            if self.inchannel: self.msg(channel, "Couldn't load module \'%s\': %s" % (moduleName, str(sys.exc_info()[1])), MSG_MAX)
            else: self.startupErr[moduleName] = sys.exc_info()[1]
            self.logger.log(LOG_ERROR, "Error loading module '%s':\n%s" % (moduleName, "".join(traceback.format_tb(sys.exc_info()[2]))))

    """ TWISTED HOOKS """

    ## Called when the bot recieves a notice.
    # @param user The user that the notice came from.
    # @param channel The channel that the notice was sent to. Will be the bot's username if the notice was sent to the bot directly and not to a channel
    def noticed(self, user, channel, message):
        self.logger.log(LOG_DEBUG, "Notice: %s" % message)
        self.runHook("noticed", user, channel, message)

    ## Called when the bot signs on to a server.
    def signedOn(self):
        self.connected = True
        self.runHook("signedOn")

        global channels
        self.join(channels[0])
        
        global password
        if password != None and password != "":
            self.msg('nickserv', "identify %s" % password, MSG_MAX)
        self.keepAlive()

    ## Called when the bot joins a channel.
    # @param channel The channel that the bot has joined.
    def joined(self, channel):
        self.joining = channel
        self.channels[channel] = {'admins': [], 'users': []}
        self.inchannel = True
        
        #Report startup errors
        if len(self.startupErr) != 0:
            self.say(channel, "Errors occured loading modules on startup:", MSG_MAX)
            for moduleName in self.startupErr:
                self.say(channel, "Couldn't load module \'%s\': %s" % (moduleName, self.startupErr[moduleName]), MSG_MAX)
                

        #Build list of admins in the channel
        self.who(channel)
    
    ## Called when the bot leaves a channel
    # @param channel The channel that the bot has left.
    def left(self, channel):
        del self.channels[channel]
        self.runHook("left", channel)
    
    def kickedFrom(self, channel, kicker, message):
        self.runHook("kickedfrom", channel, kicker, message)
        del self.channels[channel]

    ## Called when a user leaves a channel that the bot is in.
    # @param user The user that has left 'channel'.
    # @param channel The channel that 'user' has left.
    def userLeft(self, user, channel):
        user = user.split('!', 1)[0]
        self.logger.log(LOG_INFO, "User '%s' has left %s." % (user, "\#" + channel))

        if user in self.channels[channel]['admins']:
            self.channels[channel]['admins'].remove(user)
        self.channels[channel]['users'].remove(user)
        self.runHook("userleft", user, channel)

    ## Called when the bot sees a user disconnect.
    # @param user The user that has quit.
    # @param quitMessage The message that the user gave for quitting.
    def userQuit(self, user, quitMessage):
        user = user.split('!', 1)[0]
        self.logger.log(LOG_INFO, "User '%s' has quit: %s." % (user, quitMessage))

        for channel in self.channels:
            if user in self.channels[channel]['admins']:
                self.channels[channel]['admins'].remove(user)
            if user in self.channels[channel]['users']:
                self.channels[channel]['users'].remove(user)
        self.runHook("userquit", user, quitMessage)

    ## Called when the bot sees a user join a channel that it is in.
    # @param user The user that has joined.
    # @param channel The channel that the user has joined.
    def userJoined(self, user, channel):
        user = user.split('!', 1)[0]
        self.logger.log(LOG_INFO, "User '%s' has joined %s." % (user, channel))
        self.channels[channel]['users'].append(user)
        self.runHook("userjoined", user, channel)

    ## Called when the bot recieves a message from a user or channel.
    # @param user The user that the message is from.
    # @param channel The channel that the message was sent to. Will be te bot's username if the message was a private message.
    # @param message The message, derp.
    def privmsg(self, user, channel, message):
        user, self.host = user.split('!', 1)

        if channel == self.nickname: channel = user
        self.runHook("privmsg", user, channel, message)

        if channel == user: self.logger.log(LOG_DEBUG, "PM: <%s> %s" % (user, message))
        else: self.logger.log(LOG_DEBUG, '%s: <%s> %s' % (channel, user, message))

        words = message.split()
        if words[0].startswith('!'):
            self.runCmd(words[0][1:], user, channel, words[1:])
        if channel in self.channels:
            if user in self.channels[channel]['admins']:
                if words[0] == '!load': # someone wants to load a module
                    for mod in words[1:]:
                        self.loadModule(mod, channel)
                if words[0] == '!unload':
                    for mod in words[1:]:
                        if self.channels[channel]['modules'].get(mod, None) == None:
                            self.msg(channel, "Module \'%s\' wasn\'t loaded." % mod, MSG_MAX)
                        else:
                            del self.channels[channel]['modules'][mod]
                            del sys.modules[mod]
                            self.msg(channel, "Module \'%s\' unloaded." % mod, MSG_MAX)
                            self.runHook("moduleunloaded", mod)

    def action(self, user, channel, data):
        if channel == self.nickname: channel = user
        self.runHook("action", user, channel, data)
    
    ## Called when users or channel's modes are changed.
    # @param user The user who instigated the change.
    # @param channel The channel where the modes are changed. If args is empty the channel for which the modes are changing. If the changes are at server level it could be equal to 'user'.
    # @param set True if the mode(s) is being added, False if it is being removed.
    # @param modes The mode or modes which are being changed.
    # @param args Any additional information required for the mode change.
    def modeChanged(self, user, channel, set, modes, args):
        if (channel in self.channels) and (modes.startswith('q') or modes.startswith('a') or modes.startswith('o')):
            if set:
                for username in args:
                    if not username in self.channels[channel]['admins']:
                        self.channels[channel]['admins'].append(username)
            else:
                for username in args:
                    self.channels[channel]['admins'].remove(username)
        self.runHook("modechanged", user, channel, set, modes, args)

    # modbot changed its nick
    def nickChanged(self, nick):
        self.logger.log(LOG_INFO, "Nick changed to %s." % nick)
        self.runHook("nickchanged", nick)

    # user changes his/her nick
    def userRenamed(self, oldnick, newnick):
        for channel, chaninfo in self.channels.items():
            if oldnick in chaninfo['users']:
                chaninfo['users'].append(newnick)
                chaninfo['users'].remove(oldnick)
        self.runHook("userrenamed", oldnick, newnick)

    ## A function to check the liveness of the socket. This is MEANT to be implemented in twisted.
    ## Without it, modbot seems to ping periodically =\
    def keepAlive(self):
        def f():
            while self.connected:
                self.ping(network)
                time.sleep(10)
        
        def start_thread():
            thread = threading.Thread(target=f)
            thread.daemon = True
            thread.start()
        
        start_thread()
            

    """"""

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)


def configure():
    config = ConfigParser.SafeConfigParser()
    config.read('settings.conf')

    global nick
    nick = config.get('Required', 'nickname')

    global network
    network = config.get('Required', 'network')

    global port
    port = config.getint('Required', 'port')

    global usessl
    if config.has_option('Misc', 'use_ssl'):
        usessl = config.getboolean('Misc', 'use_ssl')

    global channels
    if config.has_option('Misc', 'channels'): channels = config.get('Misc', 'channels').split()
        

if __name__ == "__main__":

    configure()
    print "Nickserv Password (Enter for none):"
    password = getpass.getpass()

    print "Connecting to %s on port %s with nick '%s'" % (network, port, nick)

    if usessl: reactor.connectSSL(network, port, BotFactory(), ssl.ClientContextFactory())
    else: reactor.connectTCP(network, port, BotFactory())
    reactor.run()
