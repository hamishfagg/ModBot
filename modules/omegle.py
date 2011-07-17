"""

--- A NOTE ---

This plugin allows you to (among other functions) listen in on a conversation between other people on Omegle.com.
Omegle.com currently has no ToS or privacy statements available, and so this plugin abides by their rules and is legal.

HOWEVER the aforementioned purpose of this function IS morally challenging.
If you consider it in bad taste, don't use it.

"""



import threading #oh god
from modulecommon import *
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
	def __init__(self, mod, index):
		self.mod = mod
		self.id = None
		self.challenge = None
		self.ready = False
		self.index = index

	def get(self, page, data='', callback='event'):
		getPage(url % page, method="POST", postdata=data, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}).addCallback(getattr(self, callback))

	def connect(self, data=None):
		if data == None:
			self.get('start/?rcs=1&spid=', '', 'connect')
		
		elif data[0] == '"' and data[-1] == '"':
			self.id = data[1:-1]
			self.ready = True
			self.loop()

	def event(self, data):
		#if not data.startswith('['): return
		if data.startswith('['):
			events = simplejson.loads(data)
			#print data
			for event in events:
				if event[0] == 'connected':
					if self.challenge != None:
						self.mod.on_recaptchaResponse(True)
						self.challenge = None
					self.mod.on_connected(self.index)
			
				elif event[0] == 'gotMessage':
					self.mod.on_message(self.index, event[1])
			
				elif event[0] == 'typing':
					self.mod.on_typing(self.index)

				elif event[0] == 'stoppedTyping':
					self.mod.on_stoppedTyping(self.index)

				elif event[0] == 'strangerDisconnected':
					self.id = None
					self.mod.on_disconnected(self.index, 'peer')

				elif event[0] == 'recaptchaRequired':
					#self.mod.on_recaptcha(str(event[1]))
					getPage("http://www.google.com/recaptcha/api/challenge?k=" + str(event[1])).addCallback(self.recaptcha)

				elif event[0] == 'recaptchaRejected':
					self.mod.on_recaptchaResponse(False)
					getPage("http://www.google.com/recaptcha/api/challenge?k=" + str(event[1])).addCallback(self.recaptcha)


		elif data == 'win' and self.challenge != None:
			self.mod.on_recaptchaResponse(True)
			self.challenge = None

		self.ready = True

	def loop(self):
		def f():
			while self.id != None:
				if self.ready:
					#print 'GETTING EVENTS'
					self.get('events', 'id=%s' % self.id, 'event')
					self.ready = False
				time.sleep(1)

		def start_thread():
			thread = threading.Thread(target=f)
			thread.daemon = True
			thread.start()

		start_thread()


	def recaptcha(self, data):
		if data.find('http://goo.gl') != -1:
			self.mod.on_recaptcha(data[data.index('"id"'):].split('"')[3], self.index)
		else:
			self.challenge = data[data.index('challenge'):].split('\'')[1]
			url = '{"longUrl": "http://www.google.com/recaptcha/api/image?c=%s"}' % self.challenge
			getPage("https://www.googleapis.com/urlshortener/v1/url", method="POST", postdata=url, headers={'Content-Type': 'application/json'}).addCallback(self.recaptcha)

	def sendMsg(self, msg):
		print msg
		self.get('send', urlencode({'msg': msg, 'id': self.id}), 'msgResponse')
	def sendTyping(self):
		self.get('typing', 'id=%s' % self.id, 'msgResponse')
	def sendStoppedTyping(self):
		self.get('stoppedtyping', 'id=%s' % self.id, 'msgResponse')

	def sendCaptcha(self, response):
		self.get('recaptcha', urlencode({'id': self.id, 'challenge': self.challenge, 'response': response}))
	
	def disconnect(self):
		self.get('disconnect', 'id=%s' % self.id, 'dcResponse')

	def msgResponse(self, data):
		if data == 'win': pass #print 'Message sent'
		else: print 'MESSAGE NOT SENT'

	def dcResponse(self, data):
		if data == 'win':
			print 'Disconnected'
			self.id = None
			self.mod.on_disconnected(self.index, 'user')
		else: print 'ERROR DISCONNECTING'

class Module(irc.IRCClient):
	def __init__(self, main):
		self.main = main
		self.clients = []
		self.mode = ''
		self.party = 4
		self.startMsg = None
		self.running = False
		self.captcha = False
		self.ready = True			#Too many fucking vars


	def on_connected(self, index):
		if self.mode == 'single':
			self.main.say(self.main.factory.channel, "Now talking to a stranger. Say Hi!", MSGHACK)
			self.clients[0].sendMsg('[Surprise! You\'re actually talking to a whole IRC channel. Different users will be prefixed with their usernames so you can tell them apart.]')
		
		else:
			self.main.say(self.main.factory.channel, "%sStranger %s connected." % (COLOUR_LIGHTGREY, index), MSGHACK)
			if self.mode == 'party': self.clients[index].sendMsg('[Welcome. You\'re not actually connected to one stranger, you\'re connected to %s! Strangers are prefixed with a number so you can keep track.]\n[You are stranger number %s]' % (self.party-1, index))
			if self.running == False:
				if index != self.party-1:
					self.clients[index+1].connect() #If this is not the last client connecting, connect the next.
				else:
					if self.startMsg != None: #if this is the last connect, send any connect messages
						for client in self.clients:
							client.sendMsg(self.startMsg)
						self.startMsg = None
					self.running = True
			elif self.mode == 'party':
				for client in self.clients:
					if client.id != None and client.index != index:
						client.sendMsg('[Stranger %s connected.]' % index)
				if self.captcha or not self.ready:
					for client in self.clients:
						if client.id == None:
							client.connect()
							return
					self.captcha = False
					self.ready = True
					print 'captcha = false'
		
	def on_message(self, index, message):
		self.main.say(self.main.factory.channel, "<Stranger %s> %s" % (index, str(message)), MSGHACK)
	
		if self.mode != 'single':
			if self.mode == 'party': message = '%s: %s' % (index, message)
			for client in self.clients:
				if client.index != index and client.index != None:
					client.sendMsg(message)
	
	def on_typing(self, index):
		if self.mode == 'spy':
			index = index*(-1) + 1
			self.clients[index].sendTyping()
	
	def on_stoppedTyping(self, index):
		if self.mode == 'spy':
			index = index*(-1) + 1
			self.clients[index].sendStoppedTyping()

	def on_recaptcha(self, url, index):
		if self.running: self.captcha = True
		self.main.say(self.main.factory.channel, "%sRecaptcha required for connection %s: %s" % (COLOUR_RED, str(index), url), MSGHACK)

	def on_recaptchaResponse(self, accepted):
		if accepted: self.main.say(self.main.factory.channel, '%sRecaptcha accepted!' % COLOUR_GREEN, MSGHACK)
		else: self.main.say(self.main.factory.channel, '%sRecaptcha rejected!' % COLOUR_RED, MSGHACK)

	def on_disconnected(self, index, reason):
		if self.mode == 'party':
			for client in self.clients:
				if client.index != index and client.index != None:
					if self.captcha:
						client.sendMsg('[Stranger %s has disconnected - waiting for captcha response by an operator.]' % index)							
					else:
						client.sendMsg('[Stranger %s has disconnected - finding a new stranger.]' % index)
			if not self.captcha and self.ready and self.running: self.clients[index].connect()

		if reason == 'user':
			if self.running == False: # !disconnect has been said
				if index != self.party - 1: self.clients[index+1].disconnect()

				else:
					self.main.say(self.main.factory.channel, "%sYou have disconnected." % COLOUR_RED, MSGHACK)
					self.clients = []
					self.mode = ''
					self.running = False
					self.captcha = False
					self.ready = True
			
		elif reason == 'peer':
			self.main.say(self.main.factory.channel, "%sStranger %s has disconnected." % (COLOUR_RED, str(index)), MSGHACK)

			if self.mode == 'spy': #if we're in spy mode, convey the DC to the other client
				index = index*(-1) + 1
				print 'disconnecting client %s' % index
				self.clients[index].disconnect()

		#if len(self.clients) == 1:
		#	self.clients = []
		#	self.mode = ''
			

	def privmsg(self, user, channel, message):
		words = message.split(' ', 1)

		if words[0] == '!omegle' and self.clients == []:
			#Create first client
			if len(words) > 1:
				if words[1].startswith('spy'):
					startMsg = words[1].split(' ', 1)
					if len(startMsg) == 2: self.startMsg = startMsg[1]
					self.mode = 'spy'
					self.party = 2
					self.clients.append(Omegle(self, 0))
					self.clients.append(Omegle(self, 1))
				
				elif words[1].startswith('party'):
					party = words[1].split(' ', 1)
					if len(party) > 1:
						if int(party[1]) > 10 or int(party[1]) < 3:
							self.main.say(self.main.factory.channel, "Please choose a number of guests between 3 and 10.", MSGHACK)
							return
						self.party = int(party[1])
						self.mode = 'party'
					for i in range(self.party):
						self.clients.append(Omegle(self, i))
			else:
				self.mode = 'single'
				self.clients.append(Omegle(self, 0))				
			
			#Start first client
			self.clients[0].connect()
			
		elif words[0] == '!disconnect':
			self.running = False
			self.clients[0].disconnect()

		elif words[0] == '!cap': #captcha response
			con, response = words[1].split(' ', 1)
			con = int(con)
			if self.clients[con].challenge == None:
				self.main.say(self.main.factory.channel, "That client doesn't require a recaptcha.", MSGHACK)
			else:
				self.clients[con].sendCaptcha(response)

		elif words[0] == '!inject' and self.mode != 'single':
			conn, msg = words[1].split(' ', 1)
			if conn == 'all':
				for client in self.clients:
					if client.id != None:
						client.sendMsg(msg)
			else:
				conn = int(conn)
				self.clients[conn].sendMsg(msg)

		elif words[0] == '!kick' and self.mode != 'single':
			conn = int(words[1])
			if self.clients[conn].id != None: self.clients[conn].disconnect()

		else:
			if self.mode == 'single' and self.clients[0].id != None:
				msg = '<%s> %s' % (user, message)
				self.clients[0].sendMsg(msg)
