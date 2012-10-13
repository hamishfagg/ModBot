import omeglehandler as Omegle
import time
from constants import *

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

    clients = []
    topics = {}
    mode = None
    captcha = None
    connecting = False
    num = 0

    def cmdOmegle(self, user, args):
        if self.clients == []: # There's no session going on in this channel yet
            if len(args) == 0:
                self.mode = 'single'
                self.logger.log(LOG_DEBUG, "Starting Omegle in single mode.")
                self.clients = [Omegle.Omegle(self, 0)]

            elif args[0] == 'spy':
                self.mode = 'spy'
                self.logger.log(LOG_DEBUG, "Starting Omegle in spy mode.")
                self.clients = [Omegle.Omegle(self, 0), Omegle.Omegle(self, 1)]

            elif args[0] == 'party':
                self.mode = 'party'
                if len(args) > 1:
                    self.num = int(args[1])
                else: self.num = 4
                self.logger.log(LOG_DEBUG, "Starting Omegle in party mode.")
                
                for i in range(0, self.num):
                    self.clients.append(Omegle.Omegle(self, i))
            if self.captcha == None:
                if not self.connecting:
                    self.connecting = True
                    self.clients[0].connect()
            else:
                self.main.msg(self.main.channel, "Waiting on captcha before connecting: %s" % self.captcha[2])
        

    def cmdDisconnect(self, user, args): # It's easier to not wait for replies
        self.mode = None
        for client in self.clients: client.disconnect()
        self.main.msg(self.main.channel, "You have disconnected.")
        time.sleep(1)
        del self.clients
        self.clients = []
        self.captcha = None
        self.connecting = False
            

    def cmdKick(self, user, args):
        try:
            index = int(args[0]) #returns if an index is not specified
            if len(args) > 1:
                message = "** Stranger %s is being kicked. (Reason: %s) **" % (index, " ".join(args[1:]))
            else:
                message = "** Stranger %s is being kicked **" % str(index)
            self.sendToAll(index-1, message)
            self.clients[index-1].disconnect()
        except: pass
    
    def cmdInject(self, user, args):
        if self.mode != 'single' and len(args) > 0:
            try:
                index = int(args[0])
            except:
                index = 0

            if index == 0: # Inject to all clients
                self.sendToAll(None, " ".join(args))
            else:
                self.clients[index-1].sendMsg(" ".join(args[1:]))
    
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
        if self.mode == 'single':
            self.clients[0].sendMsg("<%s> %s" % (user.split('!', 1)[0], message))

    def action(self, user, data):
        if self.mode == 'single':
            self.clients[channel]['clients'][0].sendMsg("* %s %s" % (user, data))   

    def sendToAll(self, exclude, message):
        for client in self.clients:
            if client.index != exclude and client.index != None:
                client.sendMsg(message)

    def on_connected(self, index):
        #time.sleep(5)
        if self.mode == 'single':
            self.logger.log(LOG_INFO, "OMEGLE: * Connected to a stranger *")
            self.clients[0].sendMsg("Surprise, you're not talking to one stranger. You're actually talking to an IRC (Internet Relay Chat) channel!")
            self.main.msg(self.main.channel, "Connected to a stranger. Say hi!")
        
        elif self.mode != None:
            self.logger.log(LOG_INFO, "OMEGLE: * Stranger %s connected *" % str(index+1))
            self.main.msg(self.main.channel, "Stranger %s connected." % str(index+1))
            if self.mode == 'party':
                self.clients[index].sendMsg("Surprise! You're not talking to just one stranger, you're actually talking to %s!\nDifferent strangers are prefixed with a number so that you can tell them apart.\n- You are stranger number %s -" % (self.num, str(index+1)))
                
                self.sendToAll(index, "** Stranger %s has connected **" % str(index+1))

            #connect the next client for this channel
            if self.connectNext(): return

        # code reaches here if there are no more unconnected clients
        self.logger.log(LOG_DEBUG, "OMEGLE: All clients connected.")
        self.connecting = False

    def connectNext(self,):
        if self.captcha == None:
            for client in self.clients:
                if client.id == None:
                    client.connect()
                    return True
            return False
        else: return True # this makes on_connected() exit, and stop bothering us.
    
    def on_message(self, index, message):
        if self.mode == 'single':
            message = "Stranger: " + message
            self.logger.log(LOG_INFO, message)
            self.main.msg(self.main.channel, message.encode('ascii', 'replace'))

        elif self.mode != None:
            if self.mode == 'spy':
                newindex = index*(-1) + 1
                self.clients[newindex].sendMsg(message)
            else:
                self.logger.log(LOG_DEBUG, "OMEGLE: %s: %s" % (str(index+1), message))
                self.sendToAll(index, "%s: %s" % (str(index+1), message))
            self.main.msg(self.main.channel, "Stranger %s: %s" % (str(index+1), message.encode('ascii', 'replace')))
    
    def on_typing(self, index):
        if self.mode == 'spy':
            newindex = index*(-1) + 1
            self.clients[newindex].sendTyping()
    
    def on_stoppedTyping(self, index):
        if self.mode == 'spy':
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

    def on_disconnected(self, index, reason):

        if self.mode == 'single':
            self.main.msg(self.main.channel, "Stranger disconnected")
            self.clients = []
            self.connecting = False
            self.captcha = None
            self.mode = None
             
        elif self.mode == 'spy':
            self.main.msg(self.main.channel, "Stranger %s has disconnected." % str(index+1))
            if self.clients[index*(-1)+1].id != None:
                self.clients[index*(-1)+1].disconnect()
            self.main.msg(self.main.channel, "You have disconnected.")
            time.sleep(1)
            del self.clients
            self.clients = []
            self.connecting = False
            self.captcha = None
            self.mode = None

        elif self.mode == 'party':
            self.main.msg(self.main.channel, "Stranger %s has disconnected." % str(index+1))
            if self.captcha == None:
                self.sendToAll(index, "** Stranger %s has disconnected. Finding a new Stranger... **" % str(index+1))
                self.connectNext()
            else:
                self.sendToAll(index, "** Stranger %s has disconnected. Waiting for an operator to solve captcha before connecting another stranger.. **" % str(index+1))
                
    def getTopics(self, index):
        return self.topics.get(index, [])
