import sys
sys.path.append("modules/help")
from constants import *

class Module():
    modules = {}
    commands = {'help': 'cmdHelp'}
    hooks = {'moduleloaded': 'moduleLoaded',
             'moduleunloaded': 'moduleUnloaded'}

    def loaded(self):
        for module in self.main.modules:
            self.loadHelp(module)

    def moduleLoaded(self, module):
        self.loadHelp(module)

    def moduleUnloaded(self, module):
        del self.modules[module]

    def pad(self, str, length):
        str += ' ' * (length - len(str))
        return str

    def cmdHelp(self, user, channel, args):
        if len(args) == 0:
            msg = 'Welcome to %s help. Please type %s!help <module>%s for help with a specific module, or %s!help <module> <command>%s for help with a specific command.\nCurrently loaded modules are: ' % (self.main.username, COLOUR_BOLD, COLOUR_DEFAULT, COLOUR_BOLD, COLOUR_DEFAULT)
            for module in self.main.modules:
                if msg.endswith('are: '): msg += module
                else: msg += ', ' + module
            msg += '.'
            self.main.msg(user, msg, MSG_MAX)

        elif len(args) == 1:
            if args[0] in self.modules:
                self.main.msg(user, '%s%s%s %s' % (COLOUR_BOLD, args[0][0].upper() + args[0][1:], COLOUR_DEFAULT, self.modules[args[0]]['desc']), MSG_MAX)
                msg = ''
                cmds = self.modules[args[0]]['commands']
                for cmd in cmds:
                    msg += '%s\t%s%s%s\n' % (COLOUR_RED, self.pad('!'+cmd, 20), COLOUR_DEFAULT, cmds[cmd]['desc'])
                self.main.msg(user, msg, MSG_MAX)
            else:
                self.main.msg(user, "That module isn't loaded.", MSG_MAX)

        elif len(args) == 2:
            if args[0] in self.modules:
                if args[1] in self.modules[args[0]]['commands']:
                    command = self.modules[args[0]]['commands'][args[1]]
                    
                    self.main.msg(user, '%s!%s%s %s' % (COLOUR_BOLD, args[0].upper(), COLOUR_DEFAULT, command['desc'][0].lower() + command['desc'][1:]), MSG_MAX)
                    usage = '%s!%s%s' % (COLOUR_BOLD, args[0], COLOUR_GREEN)
                    msg = ''
                    for param in command['params']:
                        usage += ' <%s>' % param
                        paramMsg = "\n%s\t%s%s%s" % (COLOUR_GREEN, self.pad(param, 20), COLOUR_DEFAULT, command['params'][param])
                        msg += paramMsg
                        print param
                        print command['params'][param]

                    self.main.msg(user, usage, MSG_MAX)
                    self.main.msg(user, msg, MSG_MAX)
                else:
                    self.main.msg(user, "No help found for %s command in the %s module." % (args[1], args[0]), MSG_MAX)
            else:
                self.main.msg(user, "That module isn't loaded.", MSG_MAX)


        else:
                    if words[1][0] == '!':
                        words[1] = words[1][1:]
                    for module in self.main.modules:
                        if hasattr(self.main.modules[module], 'help') and words[1] in self.main.modules[module].help:
                            command = self.main.modules[module].help[words[1]]
                            
                            return
                    self.main.msg(user, 'No help found for that module or command.', MSGHACK)

    def loadHelp(self, module):
        try:
            help = __import__("%shelp" % module)
            self.modules[module] = help.help
        except:
            pass                
