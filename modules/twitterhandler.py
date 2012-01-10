import sys
import datetime
import tweepy
from twitterconf import *

#Formats a timestamp and stores it.
now = datetime.datetime.now()
timestamp = '[' + now.strftime("%Y-%m-%d  %H:%M") + '] '
tweettimestamp = '(' + now.strftime("%H:%M:%S") + ') '

def tweet(msg):
    try:
        #Tries to send a tweet via twitter and log a successsful send.
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
        api = tweepy.API(auth)
        #api.update_status(tweettimestamp + msg)
        api.update_status(msg)
        return 1
    
    except:
        #If sending fails, log the error
        error = 'Error tweeting message: ' + str(sys.exc_info()[1]) + "\n"
        return error
