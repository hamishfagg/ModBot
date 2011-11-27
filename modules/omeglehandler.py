import threading #oh god
from twisted.internet import reactor
from twisted.web.client import getPage
from twisted.python.util import println
from urllib import urlencode
import simplejson
import time
import sys

url = 'http://bajor.omegle.com/%s'
DEBUG = 1

class Omegle:
    def __init__(self, mod, channel, index):
        self.mod = mod
        self.channel = channel
        self.id = None
        self.challenge = None
        self.ready = False
        self.index = index


    def get(self, page, data='', callback='event'):
        #print "Getting %s" % page
        getPage(url % page, method="POST", postdata=data, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}).addCallback(getattr(self, callback))

    def getEvents(self):
        deff = reactor.callFromThread(getPage, url % "events", {'method': 'POST', 'postdata': 'id=%s' % self.id, 'headers': {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}})
        deff.addCallback(getAttr(self, 'event'))

    def connect(self, data=None):
        if data == None:
            self.get('start/?rcs=1&spid=', '', 'connect')
        
        elif data[0] == '"' and data[-1] == '"':
            self.id = data[1:-1]
            self.ready = True
            self.loop()
        else: print data

    def event(self, data):
        if data.startswith('['):
            events = simplejson.loads(data)
            for event in events:
                if event[0] == 'connected':
                    if self.challenge != None:
                        self.mod.on_recaptchaResponse(self.channel, self.index, True)
                        self.challenge = None
                    self.mod.on_connected(self.channel, self.index)
            
                elif event[0] == 'gotMessage':
                    self.mod.on_message(self.channel, self.index, event[1])
            
                elif event[0] == 'typing':
                    self.mod.on_typing(self.channel, self.index)

                elif event[0] == 'stoppedTyping':
                    self.mod.on_stoppedTyping(self.channel, self.index)

                elif event[0] == 'strangerDisconnected':
                    self.id = None
                    self.mod.on_disconnected(self.channel, self.index, 'peer')

                elif event[0] == 'recaptchaRequired':
                    getPage("http://www.google.com/recaptcha/api/challenge?k=" + str(event[1])).addCallback(self.recaptcha)

                elif event[0] == 'recaptchaRejected':
                    self.mod.on_recaptchaResponse(self.channel, self.index, False)
                    getPage("http://www.google.com/recaptcha/api/challenge?k=" + str(event[1])).addCallback(self.recaptcha)


        #elif data == 'win' and self.challenge != None:
        #   self.mod.on_recaptchaResponse(self.channel, self.index, True)
        #   self.challenge = None

        self.ready = True

    def recaptcha(self, data):
        if data.find('http://goo.gl') != -1:
            self.mod.on_recaptcha(self.channel, self.index, data[data.index('"id"'):].split('"')[3])
        else:
            self.challenge = data[data.index('challenge'):].split('\'')[1]
            url = '{"longUrl": "http://www.google.com/recaptcha/api/image?c=%s"}' % self.challenge
            getPage("https://www.googleapis.com/urlshortener/v1/url", method="POST", postdata=url, headers={'Content-Type': 'application/json'}).addCallback(self.recaptcha)

    def sendMsg(self, msg):
        #print "sending: %s" % msg
        self.get('send', urlencode({'msg': msg, 'id': self.id}), 'msgResponse')
    def sendTyping(self):
        self.get('typing', 'id=%s' % self.id, 'msgResponse')
    def sendStoppedTyping(self):
        self.get('stoppedtyping', 'id=%s' % self.id, 'msgResponse')

    def sendCaptcha(self, response):
        self.get('recaptcha', urlencode({'id': self.id, 'challenge': self.challenge, 'response': response}))
    
    def disconnect(self):
        self.get('disconnect', 'id=%s' % self.id, 'passFunc')
        self.id = None
        self.mod.on_disconnected(self.channel, self.index, 'user')

    def msgResponse(self, data):
        if data == 'win': pass #print 'Message sent'
        else: print 'MESSAGE NOT SENT'
    
    def loop(self):
        def f():
            while self.id != None:
                if self.ready:
                    reactor.callFromThread(self.get, 'events', 'id=%s' % self.id, 'event')
                    self.ready = False
                time.sleep(1)

        def start_thread():
            thread = threading.Thread(target=f)
            thread.daemon = True
            thread.start()

        start_thread()

    def passFunc(self, data): pass
