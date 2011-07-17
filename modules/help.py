from modulecommon import *
from colours import *

class Module(irc.IRCClient):
	
	def __init__(self, main):
		self.main = main

	def pad(self, str, length):
		str += ' ' * (length - len(str))
		return str

	def privmsg(self, user, channel, message):
		words = message.split()
		
		if words[0] == '!help':
			if len(words) == 1:
				msg = 'Welcome to %s help. Please type %s!help <module>%s for help with a specific module, or %s!help <command>%s for help with a specific command.\nCurrently loaded modules are: ' % (self.main.username, COLOUR_BOLD, COLOUR_DEFAULT, COLOUR_BOLD, COLOUR_DEFAULT)
				for module in self.main.modules:
					if msg.endswith('are: '): msg += module
					else: msg += ', ' + module
				msg += '.'
				self.main.msg(user, msg, MSGHACK)

			else:
				if words[1] in self.main.modules:
					help = self.main.modules[words[1]].help
					self.main.msg(user, '%s%s%s %s' % (COLOUR_BOLD, words[1][0].upper() + words[1][1:], COLOUR_DEFAULT, help['desc']), MSGHACK)
					msg = ''
					for section in help:
						print section
						if section == 'desc':
							pass
						else:
							msg += '%s\t%s%s%s\n' % (COLOUR_RED, self.pad('!'+section, 20), COLOUR_DEFAULT, help[section]['desc'])
					self.main.msg(user, msg, MSGHACK)
					return

				else:
					if words[1][0] == '!':
						words[1] = words[1][1:]
					for module in self.main.modules:
						if hasattr(self.main.modules[module], 'help') and words[1] in self.main.modules[module].help:
							command = self.main.modules[module].help[words[1]]
							self.main.msg(user, '%s!%s%s %s' % (COLOUR_BOLD, words[1].upper(), COLOUR_DEFAULT, command['desc'][0].lower() + command['desc'][1:]), MSGHACK)
							usage = '%s!%s%s' % (COLOUR_BOLD, words[1], COLOUR_GREEN)
							msg = ''
							for param in command['params']:
								usage += ' <%s>' % param
								paramMsg = "\n%s\t%s%s%s" % (COLOUR_GREEN, self.pad(param, 20), COLOUR_DEFAULT, command['params'][param])
								msg += paramMsg
								print param
								print command['params'][param]

							self.main.msg(user, usage, MSGHACK)
							self.main.msg(user, msg, MSGHACK)
							return
					self.main.msg(user, 'No help found for that module or command.', MSGHACK)
