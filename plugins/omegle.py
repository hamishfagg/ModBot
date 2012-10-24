import omeglehandler as Omegle
from time import sleep
from constants import *



### CONSTANTS FOR EACH OPERATING MODE ###

# 0- Single (client talked to IRC chan)
# 1- Spy (watch a normal omegle conversation - they have no idea you're watching)
# 2- Party! (connect 2-9000 clients together, each is given a number so they can tell eachother apart)

MODENAMES = ["single", "spy", "party"]
GREETINGS = [
    "Surprise, you're not talking to one stranger. You're actually talking to an IRC (Internet Relay Chat) channel!%s%s",
    "%s%s",
    "Surprise! You're not talking to just one stranger, you're actually talking to %s!\nDifferent strangers are prefixed with a number so that you can tell them apart.\n*** You are stranger number %s ***"
]
NUM_CLIENTS = [1, 2, 4] # 4 is the default for party.
DEFAULT_PARTY_NUM = 4


class Plugin():
    depends = ['logger']
    hooks = {'privmsg': 'privmsg'}
    commands = {'omegle': 'cmdOmegle',
                'disconnect': 'cmdDisconnect',
                'cap': 'cmdCap',
                'kick': 'cmdKick',
                'inject': 'cmdInject',
                'topics': 'cmdTopics',
                'addtopics': 'cmdAddTopic',
                'deltopics': 'cmdDelTopics'
                }

    clients = {}
    topics = {}
    mode = None
    captcha = None
    num = 4

    
    def cmdOmegle(self, user, args):
        if self.clients == {}: # There's no session going on in this channel yet
            if len(args) == 0:
                self.mode = 0
            elif args[0] in MODENAMES:
                self.mode = MODENAMES.index(args[0])
                self.logger.log(LOG_DEBUG, "Starting Omegle in %s mode." % MODENAMES[self.mode])
            else: self.main.msg(self.main.channel, "Invalid Omegle mode. Modes are: %s" % ", ".join(MODENAMES))

            self.clients[0] = Omegle.Omegle(self, 0)
            self.clients[0].connect()


    def cmdDisconnect(self, user, args): # It's easier to not wait for replies
        self.mode = None
        NUM_CLIENTS[2] = DEFAULT_PARTY_NUM
        
        if self.clients != {}:
            for client in self.clients: self.clients[client].disconnect()
            self.main.msg(self.main.channel, "You have disconnected.")
            sleep(0.5)
            self.clients = {}
        self.captcha = None
        self.logger.log(LOG_DEBUG, "Omegle stopped.")
        

    def cmdKick(self, user, args):
        if self.mode == 2:
            try:
                index = int(args[0]) #returns if an index is not specified
                if len(args) > 1:
                    message = "** Stranger %s is being kicked. (Reason: %s) **" % (index, " ".join(args[1:]))
                else:
                    message = "** Stranger %s is being kicked **" % str(index)
                self.sendToAll(index-1, message)
                self.clients[index-1].disconnect()
                sleep(0.5)
                del self.clients[index-1]
                self.main.msg(self.main.channel, "Kicked,")
                self.connectNext()
            except: pass
    
    def cmdInject(self, user, args):
        if self.mode != 0 and len(args) > 0:
            try:
                index = int(args[0])
                self.clients[index-1].sendMsg(" ".join(args[1:]))
            except:
                self.sendToAll(None, " ".join(args))
    
    def cmdCap(self, user, args):
        if len(args) > 0:
            self.clients[self.captcha[0]].sendCaptcha(" ".join(args))

    def cmdTopics(self, user, args):
        if len(self.topics) == 0:        
            self.main.msg(self.main.channel, "No current topics.")
        else:
            self.main.msg(self.main.channel, "Current topics:")
        for client in self.topics:
            self.main.msg(self.main.channel, "Client %s: %s" % (client+1, ", ".join(self.topics[client])))

    def cmdAddTopic(self, user, args):
        try:
            client = int(args[0])-1
        except:
            self.main.msg(self.main.channel, "Usage: !addtopic <client> <topic>")
            return
        
        if not client in self.topics: self.topics[client] = []
        self.topics[client].extend(args[1:])
        self.main.msg(self.main.channel, "Done.")
    
    def cmdDelTopics(self, user, args):
        if len(args) > 0:
            try:
                del self.topics[int(args[0])-1]
            except: return
        else:
            self.topics = {}
        self.main.msg(self.main.channel, "Done.")


    def privmsg(self, user, channel, message):
        if self.mode == 0:
            self.clients[0].sendMsg("<%s> %s" % (user.split('!', 1)[0], message))

    def action(self, user, data):
        if self.mode == 'single':
            self.clients[0].sendMsg("* %s %s" % (user, data))   

    def sendToAll(self, exclude, message):
        for client in self.clients:
            if self.clients[client].index != None and self.clients[client].index != exclude:
                self.clients[client].sendMsg(message)

    def on_connected(self, index):
        if self.mode == 0:
            self.logger.log(LOG_INFO, "OMEGLE: * Connected to a stranger *")
            self.main.msg(self.main.channel, "** Connected to a stranger. Say hi! **")
            args = ["", ""]

        
        else:
            self.logger.log(LOG_INFO, "OMEGLE: * Stranger %s connected *" % str(index+1))
            self.main.msg(self.main.channel, "** Stranger %s connected **" % str(index+1))
            if self.mode == 2:
                self.sendToAll(index, "** Stranger %s has connected **" % str(index+1))
                args = [NUM_CLIENTS[self.mode], str(index+1)]
            else: args = ["", ""]

            self.clients[index].sendMsg(GREETINGS[self.mode] % (args[0], args[1]))

            self.connectNext()

        

    def connectNext(self,):
        if self.captcha == None:
            for i in range(NUM_CLIENTS[self.mode]):
                if self.clients.get(i, None) == None:
                    self.clients[i] = Omegle.Omegle(self, i)
                    self.clients[i].connect()
                    return
            self.logger.log(LOG_DEBUG, "OMEGLE: All clients connected.")

    
    def on_message(self, index, message):
        if self.mode == 0:
            message = "Stranger: " + message
            self.logger.log(LOG_INFO, message)
        else:
            if self.mode == 1:
                newindex = index*(-1) + 1
                self.clients[newindex].sendMsg(message)
            else:
                self.sendToAll(index, "%s: %s" % (str(index+1), message))

        message = "Stranger %s: %s" % (str(index+1), message)
        self.main.msg(self.main.channel, message.encode('ascii', 'replace'))
        self.logger.log(LOG_DEBUG, "OMEGLE: %s" % (message))

    
    def on_typing(self, index):
        if self.mode == 1:
            newindex = index*(-1) + 1
            self.clients[newindex].sendTyping()
    
    def on_stoppedTyping(self, index):
        if self.mode == 1:
            newindex = index*(-1) + 1
            self.clients[newindex].sendStoppedTyping()

    def on_recaptcha(self, index, url):
        self.main.msg(self.main.channel, "Recaptcha required: %s" % url)
        self.captcha = [index, url] #this is to keep track of where the captcha is needed, and to stop new clients connecting

    def on_recaptchaResponse(self, index, accepted):
        if accepted == True:
            self.captcha = None
            self.main.msg(self.main.channel, 'Recaptcha accepted!')
        else: self.main.msg(self.main.channel, 'Recaptcha rejected!')

    def on_commonLikes(self, index, likes):
        self.main.msg(self.main.channel, "Stranger %s likes: %s" % (str(index+1), ", ".join(likes)))

    def on_disconnected(self, index, reason):
        del self.clients[index]
        dc = False
        if self.mode == 0:
            message = "** Stranger disconnected **"
            dc = True
             
        else:
            message = "** Stranger %s has disconnected **" % str(index+1)

            if self.mode == 1:
                dc = True

            elif self.captcha == None:
                self.sendToAll(index, "** Stranger %s has disconnected. Finding a new Stranger... **" % str(index+1))
                self.connectNext()
            else:
                self.sendToAll(index, "** Stranger %s has disconnected. Waiting for an operator to solve captcha before connecting another stranger.. **" % str(index+1))
        self.main.msg(self.main.channel, message)
        if dc: self.cmdDisconnect(None, None)
                
    def getTopics(self, index):
        return self.topics.get(index, [])
