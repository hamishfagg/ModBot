help = {
		'desc': 'provides channel polls for users to vote on.',
		'commands': {
			'newpoll': {
				'desc': 'Start a new poll - closes any current poll.',
				'params': {
					'question': 'A yes/no question for people to vote on'
				}
			},
			'poll': {
				'desc': 'Prints the current poll and votes.',
				'params': {}
			},
			'vote': {
				'desc': 'Vote on the current poll.',
				'params': {
					'vote': '"yes" or "no", depending on your outlook on life.'
				}
			},
			'closepoll': {
				'desc': 'Close the current poll.',
				'params': {}
			}
		}
	}
