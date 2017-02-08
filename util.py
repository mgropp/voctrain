def get_translations(duolingo, words, source, target):
	size = 32
	slices = [ words[start:(start+size)] for start in range(0, len(words), size) ]
	
	translations = dict()
	for word_slice in slices:
		translations.update(duolingo.get_translations(word_slice, source=source, target=target))
	
	return translations
