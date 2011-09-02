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
		else: print data

	def event(self, data):
		#if not data.startswith('['): return
		if data.startswith('['):
			events = simplejson.loads(data)
			#print data
			for event in events:
				if event[0] == 'connected':
					if self.challenge != None:
						self.mod.on_recaptchaResponse(self.index, True)
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
					getPage("http://www.google.com/recaptcha/api/challenge?k=" + str(event[1])).addCallback(self.recaptcha)

				elif event[0] == 'recaptchaRejected':
					self.mod.on_recaptchaResponse(self.index, False)
					getPage("http://www.google.com/recaptcha/api/challenge?k=" + str(event[1])).addCallback(self.recaptcha)


		elif data == 'win' and self.challenge != None:
			self.mod.on_recaptchaResponse(self.index, True)
			self.challenge = None

		self.ready = True

	def recaptcha(self, data):
		if data.find('http://goo.gl') != -1:
			self.mod.on_recaptcha(self.index, data[data.index('"id"'):].split('"')[3])
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
