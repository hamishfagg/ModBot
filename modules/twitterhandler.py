import sys
import datetime
import tweepy
from twitterconf import *

CONSUMER_KEY = 'JuCrTZUD37KSf5TdFhDPw'
CONSUMER_SECRET = 'S8I5hMlogCkcJfWwtcK9o3khwxBTQint90bmxrKr8'
ACCESS_KEY = '120972968-Iu9rETYugCyZPeJjZwT5E9VD8Z7iWkwRyNKe8rvg'
ACCESS_SECRET = 'xPlNdp4eFE6bea8HLBX4paaiMiaIzyxNcZDGbfhCM'

#Formats a timestamp and stores it.
now = datetime.datetime.now()
timestamp = '[' + now.strftime("%Y-%m-%d  %H:%M") + '] '
tweettimestamp = '(' + now.strftime("%H:%M:%S") + ') '

def log(msg):
    log = open('/home/mystx/scripts/log.txt', 'a')
    log.write(timestamp + msg)
    log.close()

def tweet(msg):
	try:
    		#Tries to send a tweet via twitter and log a successsful send.
    		#print 'SENDING MESSAGE: %s' % (msg)
    		auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	    	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	    	api = tweepy.API(auth)
		#api.update_status(tweettimestamp + msg)
		api.update_status(msg)
	    	logmsg = 'Sent tweet ' + "\"" + msg + "\".\n"
    		log(logmsg)
		return 1
    
	except:
		#If sending fails, log the error
	    	error = 'ERROR: tweeting message: ' + str(sys.exc_info()[1]) + "\n"
	    	log(error)
		return 0
