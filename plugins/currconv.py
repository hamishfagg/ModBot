from constants import *
import subprocess

class Plugin():

    commands = {'convert': 'convert'}

    def convert(self, user, args):
        args = args[1:]
        print len(args)
        print args 
        if len(args) == 3 and len(args[1]) == 3 and len(args[2]) == 3:
            try:
                quantity = int(args[0])
                out, err = subprocess.Popen('curl "http://www.google.com/ig/calculator?hl=en&q={0}{1}=?{2}"'.format(quantity, args[1], args[2]), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                
                #parse
                if out.split('error: "')[1][0] != '"':
                    self.main.msg(self.main.channel, "The currency converter returned an error. Are your currency codes right?\nA list of all currency codes is here: http://www.google.com/finance/converter")
                    return

                lhs = out.split('lhs: "')[1].split('"')[0]
                rhs = out.split('rhs: "')[1].split('"')[0]
                self.main.msg(self.main.channel, "{0} = {1}".format(lhs, rhs))
                
                return
                
            except: pass

        self.main.msg(self.main.channel, "Usage:{0} !convert <quantity> <from> <to>{1}\ne.g.{0} !convert 1 NZD USD{1}".format(COLOUR_BOLD, COLOUR_DEFAULT))
