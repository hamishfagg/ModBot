from constants import *
import datetime

class Module():

    def log(self, level, message):
        now = datetime.datetime.now()
        timestamp = '[%s]' % now.strftime("%Y-%m-%d %H:%M")
        if level == 1: tag   = '  ERROR'
        elif level == 2: tag = 'WARNING'
        elif level == 3: tag = '   INFO'
        else: tag            = '  DEBUG'

        print "%s %s: %s" % (timestamp, tag, message)
