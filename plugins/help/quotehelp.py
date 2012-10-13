help = {
	'desc': 'searches, prints or adds new quotes. Tweets new quotes as they are added (if the Twitter module is loaded)',
	'commands': {
		'quote': {
			'desc': 'Searches the quote database given a search term. If none is given, this command prints the latest quote.',
			'params': {
				'searchstring': 'String term to search for in the quote database (optional).'
			}
		},
		'newquote': {
			'desc': 'Adds a new quote to the database. Tweets the new quote given it is short enough and the Twitter module is loaded.',
			'params': {
				'quote': 'Quote to add to the database.'
			}
		},
		'randquote': {
			'desc': 'Prints a random quote.',
			'params': {}
		}
	}
}
