import sys
import getpass

sys.path.append("plugins")
from constants import *
import ConfigParser
import logger

import threading
import time
import traceback

from twisted.internet import ssl, reactor, protocol, stdio
from twisted.words.protocols import irc
from twisted.protocols import basic

settings = {}

class Bot(irc.IRCClient):

    ## Instance init.
    def __init__(self):
        threading.Timer(60, self.minuteTimer).start()
        self.logger = logger.Plugin()
        self.startupErr = {}

        self.connected = False
        self.inchan = False
        self.settings = settings
        self.nickname = settings['Required']['nickname']
        self.channel = settings['Required']['channel']
        self.admins = settings['Required']['admins']
        self.plugins = {}
        
    def minuteTimer(self):
        reactor.callFromThread(self.runHook, "minutetimer")    
        threading.Timer(60, self.minuteTimer).start()

    ## List users in 'channel'. Used for gaining user modes on join.
    # @param channel The channel for which to list names.
    #def who(self, channel):
    #    if PREFIX_OWNER == '':
    #        self.mapPrefixes()
    #    self.logger.log(LOG_DEBUG, "Retreiving user list.")
    #    self.sendLine('WHO %s' % channel)

    ## Recieve a WHO reply from the server.
    # @param nargs A list of arguments including modes etc. See twisted documentation for details.
    #def irc_RPL_WHOREPLY(self, *nargs):
    #    prefix = nargs[1][6]
    #    uname = nargs[1][5]
    #    if not uname in self.users:
    #        self.users[uname] = User(uname)                                             # Add the user to the user list
    #
    #    if prefix.endswith(PREFIX_OWNER) or prefix.endswith(PREFIX_ADMIN) or prefix.endswith(PREFIX_OPERATOR):
    #        self.channels[self.joining].admins[uname] = self.users[uname]           # Add user to channel's list of admins
    #        self.users[uname].admin[self.joining] = self.channels[self.joining]     # Add channel to user's list of admin'd channels

    #    self.users[uname].channels[self.joining] = self.channels[self.joining]      # Add the channel to the user's channel list
    #    self.channels[self.joining].users[uname] = self.users[uname]                # Add the user to the channel's user list
    #    self.runHook("irc_rpl_whoreply", self.joining, *nargs)

    ## Called when WHO output is complete.
    # @param nargs A list of arguments including modes etc. See twisted documentation for details.
    #def irc_RPL_ENDOFWHO(self, *nargs):
    #    self.logger.log(LOG_INFO, "Finished Joining %s.\n\t\t\t\tFound users: %s.\n\t\t\t\tFound admins: %s." % (self.joining, ", ".join(self.channels[self.joining].users), ", ".join(self.channels[self.joining].admins)))
    #    self.runHook("joined", self.joining, self.joining) #This is to stop the hook being run before user lists are populated
    #    self.runHook("irc_rpl_endofwho", self.joining, *nargs)

    #    for channel in self.channelsConf:
    #        if (not channel in self.channels) and self.channelsConf[channel]['autojoin'] == 'yes':
    #            self.join(channel)
    #            break

    def topicUpdated(self, user, channel, newTopic):
        self.runHook("topicupdated", channel, user, channel, newTopic)
        
    ## Runs a given function in all loaded plugins. Handles any resulting errors.
    def runHook(self, hook, *args):
        self.logger.log(LOG_DEBUG, "Running hook %s" % hook)

        for plugin in self.plugins:
            functionName = self.plugins[plugin].hooks.get(hook, None)
            if functionName != None:
                try:
                    function = getattr(self.plugins[plugin], functionName)
                    function(*args)
                except:
                    # Print the error
                    self.say(self.channel, "Error running %s hook in plugin %s: %s" % (hook, plugin, str(sys.exc_info()[1])))
                    self.logger.log(LOG_ERROR, "Error running %s hook in plugin %s\n%s\n%s\n" % (hook, plugin, traceback.format_exc(), str(sys.exc_info()[1])))

    def runCmd(self, cmd, user, args):
        self.logger.log(LOG_DEBUG, "Running cmd %s" % cmd)

        for plugin in self.plugins:
            functionName = self.plugins[plugin].commands.get(cmd, None)
            if functionName != None:
                try:
                    function = getattr(self.plugins[plugin], functionName)                    
                    function(user, args)
                except Exception,e:
                    # Print the error
                    self.say(self.channel, "Error running %s command in plugin %s: %s" % (cmd, plugin, str(sys.exc_info()[1])), MSG_MAX)
                    self.logger.log(LOG_ERROR, "Error running %s command in plugin %s\n%s\n%s\n%s\n%s\n" % (cmd, plugin, "".join(traceback.format_tb(sys.exc_info()[2])), sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
    
    ## Tries to load a given plugin name and handles any errors. If the plugin is already loaded, it uses 'reload' to reload the plugin.
    def loadPlugin(self, pluginName):
        self.logger.log(LOG_DEBUG, "Attempting to load '%s'" % (pluginName))
        try:
            #if pluginName in sys.modules:
            #    self.logger.log(LOG_DEBUG, "%s is in sys.modules - reloading" % pluginName)
            #    del sys.modules[pluginName]
                # Re-init each plugin() instance

            module = __import__(pluginName)

            plugin = module.Plugin()        #Get an object containing the 'plugin' class of the given plugin
            plugin.main = self

            # Check dependancies
            if hasattr(plugin, 'depends'):
                for depend in plugin.depends:
                    if depend in self.plugins:
                        self.logger.log(LOG_DEBUG, " - Dependancy '%s' is loaded" % depend)
                        setattr(plugin, depend, self.plugins[depend]) # TODO: Here, a dep is shared among other plugins. is this right?
                    else:
                        self.logger.log(LOG_ERROR, "Failed to load %s: A dependancy (%s) is not loaded." % (pluginName, depend))
                        self.msg(self.channel, "Couldn't load plugin \'%s\': A dependancy (%s) is not loaded." % (pluginName, depend), MSG_MAX)
                        return
            else:
                plugin.depends = {}
                self.logger.log(LOG_DEBUG, "No dependancies found.")
            if not hasattr(plugin, 'commands'): plugin.commands = {}
            if not hasattr(plugin, 'hooks'): plugin.hooks = {}
            
            self.plugins[pluginName] = plugin
            
            self.logger.log(LOG_INFO, "Plugin '%s' has been loaded." % (pluginName))
            if self.inchan: #Stop calls to 'msg' when startup plugins are loaded
                self.msg(self.channel, "%sLoaded plugin \'%s\'." % (COLOUR_GREY, pluginName), MSG_MAX)
            if hasattr(plugin, 'loaded'):
                plugin.loaded() # All dependancies have been mapped, and the plugin is now loaded
            self.runHook("pluginloaded", pluginName)

        except:
            if pluginName in self.plugins: del self.plugins[pluginName]
            if sys.modules.get(pluginName, None) != None: del sys.modules[pluginName]

            if self.inchan: self.msg(self.channel, "Couldn't load plugin \'%s\': %s" % (pluginName, str(sys.exc_info()[1])), MSG_MAX)
            else: self.startupErr[pluginName] = sys.exc_info()[1]
            self.logger.log(LOG_ERROR, "Error loading plugin '%s':\n%s" % (pluginName, "".join(traceback.format_tb(sys.exc_info()[2]))))

    """ TWISTED HOOKS """

    ## Called when the bot recieves a notice.
    def noticed(self, user, channel, message):
        self.logger.log(LOG_DEBUG, "Notice: %s" % message)
        self.runHook("noticed", user, channel, message)

    ## Called when the bot signs on to a server.
    def signedOn(self):
        self.factory.curr_instance = self
        self.connected = True
        time.sleep(3) #TODO
        self.runHook("signedOn")
        
        global password
        if password != None and password != "":
            self.msg('nickserv', "identify %s" % password)
        self.keepAlive()

        self.join(self.channel)

    ## Called when the bot joins a channel.
    def joined(self, channel): # TODO changing channels
        self.logger.log(LOG_INFO, "Joined %s" % channel)
        self.channel = channel
        if self.settings['Misc'].get('plugins', None) != None:
            for plugin in self.settings['Misc']['plugins']:
                self.loadPlugin(plugin)

        self.inchan = True
        
        #Report startup errors
        if len(self.startupErr) != 0:
            self.msg(self.channel, "Errors occured loading plugins on startup:")
            for pluginName in self.startupErr:
                self.msg(self.channel, "Couldn't load plugin \'%s\': %s" % (pluginName, self.startupErr[pluginName]))
                

    ## Called when the bot leaves a channel
    def left(self, channel):
        self.runHook("left", channel)
        self.logger.log(LOG_INFO, "Left channel: %s" % channel)
    
    def kickedFrom(self, channel, kicker, message):
        self.runHook("kickedfrom", channel, kicker, message)
        self.logger.log(LOG_WARNING, "Kicked from %s: %s" % (channel, message))

    ## Called when a user leaves a channel that the bot is in.
    def userLeft(self, user, channel):
        self.logger.log(LOG_INFO, "User '%s' has left %s." % (user.split('!', 1)[0], channel))
        self.runHook("userleft", user, channel)

    ## Called when the bot sees a user disconnect.
    def userQuit(self, user, quitMessage):
        self.logger.log(LOG_INFO, "User '%s' has quit: %s." % (user.split('!', 1)[0], quitMessage))
        self.runHook("userquit", user, quitMessage)

    ## Called when the bot sees a user join a channel that it is in.
    def userJoined(self, user, channel):
        self.logger.log(LOG_INFO, "User '%s' has joined %s." % (user.split('!', 1)[0], channel))
        self.runHook("userjoined", user, channel)

    def action(self, user, channel, data):
        self.logger.log(LOG_DEBUG, "* %s %s" % (user, data))
        self.runHook("action", user, channel, data)

    ## Called when the bot recieves a message from a user or channel.
    def privmsg(self, user, channel, message):
        userName, self.host = user.split('!', 1)
        words = message.split()

        self.runHook("privmsg", user, channel, message)

        if channel == self.nickname: self.logger.log(LOG_DEBUG, "PM: <%s> %s" % (userName, message))
        else: self.logger.log(LOG_DEBUG, '<%s> %s' % (userName, message))

        if words[0].startswith('!'):
            self.runCmd(words[0][1:].lower(), userName, words[1:])

        if userName in self.admins:
            if words[0] == '!load': # someone wants to load a plugin
                for plugin in words[1:]:
                    self.loadPlugin(plugin)
            elif words[0] == '!unload':
                for plug in words[1:]:
                    if self.plugins.get(plug, None) == None:
                        self.msg(self.channel, "Plugin \'%s\' wasn\'t loaded." % plug)
                    else:
                        for pluginName, plugin in self.plugins.items():
                            if plug in plugin.depends:
                                self.logger.log(LOG_WARNING, "Cannot unload %s, another plugin (%s) depends on it." % (plug, pluginName))
                                self.msg(self.channel, "Cannot unload %s, another plugin (%s) depends on it." % (plug, pluginName))
                                return
                        del self.plugins[plug]
                        del sys.modules[plug]
                        self.msg(self.channel, "Plugin \'%s\' unloaded." % plug)
                        self.runHook("pluginunloaded", channel, plug)
    
    ## Called when users or channel's modes are changed.
    def modeChanged(self, user, channel, set, modes, args):
        #if (channel in self.channels) and (modes.startswith('q') or modes.startswith('a') or modes.startswith('o')):
        #    for username in args:
        #        if set:
        #            self.users[username].admin[channel] = self.channels[channel]
        #            self.channels[channel].admins[username] = self.users[username]
        #        else:
        #            del self.channels[channel].admins[username]
        #            del self.users[username].admin[channel]
        #            
        #if channel == self.nickname: channel = None
        self.runHook("modechanged", user, channel, set, modes, args)

    # modbot changed its nick
    def nickChanged(self, nick):
        self.logger.log(LOG_INFO, "Nick changed to %s." % nick)
        self.runHook("nickchanged", nick)

    # user changes his/her nick
    def userRenamed(self, oldnick, newnick):
        self.runHook("userrenamed", oldnick, newnick)

    #def mapPrefixes(self):
    #    global PREFIX_OWNER, PREFIX_ADMIN, PREFIX_OPERATOR, PREFIX_HALFOP
    #    prefixes = self.supported.getFeature('PREFIX')

    #    if prefixes.get(MODE_OWNER, None) != None: PREFIX_OWNER = prefixes[MODE_OWNER][0]
    #    else: PREFIX_OWNER = "N/A"
    #    if prefixes.get(MODE_ADMIN, None) != None: PREFIX_ADMIN = prefixes[MODE_ADMIN][0]
    #    else: PREFIX_ADMIN = "N/A"
    #    if prefixes.get(MODE_OPERATOR, None) != None: PREFIX_OPERATOR = prefixes[MODE_OPERATOR][0]
    #    else: PREFIX_OPERATOR = "N/A"
    #    if prefixes.get(MODE_HALFOP, None) != None: PREFIX_HALFOP = prefixes[MODE_HALFOP][0]
    #    else: PREFIX_HALFOP = "N/A"

    ## A function to check the liveness of the socket. This is MEANT to be implemented in twisted.
    ## Without it, modbot seems to pingout periodically =\
    def keepAlive(self):
        def f():
            while self.connected:
                self.ping(self.settings['Required']['network'])
                time.sleep(10)
        
        def start_thread():
            thread = threading.Thread(target=f)
            thread.daemon = True
            thread.start()
        
        start_thread()
            

    def msg(self, channel, message, max=MSG_MAX):
        if channel != 'console':
            irc.IRCClient.msg(self, channel, message, max)
        else:
            print "-- "+message

    """"""

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)

class Echo(basic.LineReceiver):
    from os import linesep as delimiter
    def __init__(self, *args, **kwargs):
        self.fact = ""

    def lineReceived(self, line):
        channel = self.fact.curr_instance.settings['Required']['nickname']
        self.fact.curr_instance.privmsg("console!console", channel, " ".join(line.split()))

def configure():
    # Read settings
    config = ConfigParser.SafeConfigParser()
    config.read('settings.conf')

    global settings
    for section in config.sections():
        settings[section] = {}
        for option in config.options(section):
            settings[section][option] = config.get(section, option)


configure()
print "Nickserv Password (Enter for none):"
password = getpass.getpass()

echoInstance = Echo()
factory = BotFactory()
echoInstance.fact = factory

requiredSettings = settings['Required']
usessl = settings['Misc'].get('use_ssl', None)
usessl = (usessl == 'true' or usessl == 'on' or usessl == 'yes' or usessl == '1')

stdio.StandardIO(echoInstance)

if usessl: reactor.connectSSL(requiredSettings['network'], int(requiredSettings['port']), factory, ssl.ClientContextFactory())
else: reactor.connectTCP(requiredSettings['network'], int(requiredSettings['port']), factory)
reactor.run()
