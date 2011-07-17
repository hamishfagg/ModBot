from modulecommon import *

class Module(irc.IRCClient):
	help = {
			'desc': 'This is the module description',
			'command':
			{
				'desc': 'Command description.', 
				'params':
			{
					'param1': 'Param1 info',
					'param2': 'Param2 info'
				}
			},
			'command2': {
				'desc': 'Command2 desc'}
		}
	def __init__(self, main):
		pass
