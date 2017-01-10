#!/usr/bin/env python3
import argparse
import duolingo
import colorama
import signal

from auth import user, password
from voctrain import VocTrainer
import audio

# TODO:
# (Aussprachepartikel)
# avant (zeitlich), devant (räumlich)
# unbestimmter Pluralartikel

def choose_skill(skills):
	print(colorama.Fore.WHITE + colorama.Style.BRIGHT + "Choose a skill!" + colorama.Style.RESET_ALL)
	for n, s in zip(range(1, len(skills)+1), skills):
		if float(s["progress_percent"]) < 100:
			progress = ", %s%.0f%%%s" % (
				colorama.Fore.MAGENTA,
				float(s["progress_percent"]),
				colorama.Style.RESET_ALL
			)
		else:
			progress = ""
		
		if s["strength"] == 1.0:
			strength = "%s%.2f%s" % (colorama.Fore.GREEN, s["strength"], colorama.Style.RESET_ALL)
		else:
			strength = "%s%.2f%s" % (colorama.Fore.YELLOW, s["strength"], colorama.Style.RESET_ALL)
		
		print(
			"%s%2s)%s %s (%s%s)" % (
				colorama.Fore.WHITE + colorama.Style.BRIGHT,
				n,
				colorama.Style.RESET_ALL,
				s["title"], strength, progress
			)
		)
	
	while True:
		try:
			skill_index = input(colorama.Fore.YELLOW + ">>> " + colorama.Style.RESET_ALL)
		except EOFError:
			print()
			return None
		
		try:
			skill_index = int(skill_index.strip())
		except:
			continue
		
		if 1 <= skill_index <= len(skills):
			skill = skills[skill_index - 1]
			break
	
	return skill


def get_all_skills(dl, lang):
	skills = [skill for skill in dl.user_data.language_data[lang]['skills']]
	
	dl._compute_dependency_order(skills)
	
	return list(sorted(skills, key=lambda skill: skill['dependency_order']))


def get_started_skills(dl, lang):
	skills = [skill for skill in dl.user_data.language_data[lang]['skills']]
	
	dl._compute_dependency_order(skills)
	
	return [ skill for skill in
		sorted(skills, key=lambda skill: skill['dependency_order'])
		if float(skill["progress_percent"]) > 0
	]


def get_words(skill_name, vocab_overview):
	# skill["words"] appears to be incomplete
	#words = []
	#print(vocab_overview)
	#for lexeme in skill["known_lexemes"]:
	#	print(lexeme)
	#	w = [ v["word_string"] for v in vocab_overview if v["lexeme_id"] == lexeme ]
	#	if len(w) == 0:
	#		print("ERROR: Lexeme not found: %s" % lexeme)
	#	else:
	#		words.append(w[0])
	#
	#return words
	
	return [ v["word_string"] for v in vocab_overview if v["skill"] == skill_name ]


def on_input():
	try:
		return input(
			colorama.Fore.YELLOW +
			">>> " +
			colorama.Style.RESET_ALL
		)
	except EOFError:
		print()
		return None


def print_summary(voc_items):
	print()
	print(
		colorama.Fore.BLUE + colorama.Style.BRIGHT +
		"Summary" +
		colorama.Style.RESET_ALL
	)
	
	v = [ x for x in voc_items if x.bad > 0 ]
	v = sorted(v, key=lambda x: -x.bad)
	for item in v:
		print(
			"%s%2d %s%s" % (
				colorama.Fore.RED + colorama.Style.BRIGHT,
				item.bad, colorama.Style.RESET_ALL,
				item.solution
			)
		)
	return "\n".join(( x.solution for x in v ))


def main(args):
	print("You can press Ctrl+D to quit.")
	print()
	
	dl = duolingo.Duolingo(user, password)
	
	skills = get_started_skills(dl, args.target)
	skills = sorted(skills, key=lambda x: (int(x["coords_y"]), int(x["coords_x"])))
	if args.debug:
		print(skills)
	
	skill = choose_skill(skills)
	if skill is None:
		return
	
	words = get_words(
		skill["title"],
		dl.get_vocabulary(args.target)["vocab_overview"]
	
	)
	if args.debug:
		print("--- words ---")
		print(words)
	
	translations_t2s = dl.get_translations(
		words,
		source=args.source,
		target=args.target
	)
	
	if args.debug:
		print("--- t2s ---")
		print(translations_t2s)
	
	if args.t2s:
		translations = translations_t2s
		vocabulary = [ ([x], y, x, None, "%s -> %s" % (x, ", ".join(y))) for x, y in translations.items() ]
	else:
		translations_s2t = dl.get_translations(
			list(set(( x for sl in translations_t2s.values() for x in sl  ))),
			source=args.target,
			target=args.source
		)
		
		# try to avoid inconsistencies in duolingo data, e.g.:
		# jeudis -> [Donnerstage]
		# Donnerstage -> []
		for s, tt in list(translations_s2t.items())[:]:
			if len(tt) == 0:
				# find translation in t2s data
				tt = [ t for t, ss in translations_t2s.items() if s in ss ]
				if len(tt) == 0:
					raise Exception("No translation found for »%s« -- this should not happen." % s)
				translations_s2t[s] = tt
		
		if args.debug:
			print("--- s2t ---")
			print(translations_s2t)
		
		vocabulary = []
		for t, ss in translations_t2s.items():
			# this would work if duolingo's translations were consistent :(
			#translation_set = None
			#for s in ss:
			#	if translation_set is None:
			#		translation_set = set(translations_s2t[s])
			#	else:
			#		translation_set = translation_set & set(translations_s2t[s])
			
			#if len(translation_set) == 0:
			
			translation_set = set()
			for s in ss:
				translation_set = translation_set.union(translations_s2t[s])
			
			vocabulary.append(( ss, list(translation_set), None, t, "%s -> %s" % (t, ", ".join(ss))))
	
	if args.debug:
		print("--- vocabulary ---")
		print(vocabulary)
	
	if len(vocabulary) == 0:
		print("No words found!")
		return False
	
	def on_prompt(item):
		print(
			colorama.Fore.WHITE + colorama.Style.BRIGHT +
			item.get_prompt() +
			colorama.Style.RESET_ALL
		)
		if item.main_l1 is not None:
			if not args.no_audio:
				audio.play_audio(item.main_l1, dl, args.target)
	
	def on_solution(item, answer, correct):
		if correct:
			print(colorama.Fore.GREEN + ("Correct! (%d/%d)" % (item.total - item.bad, item.total)) + colorama.Style.RESET_ALL)
		else:
			print(colorama.Fore.RED + ("Wrong! (%d/%d)" % (item.total - item.bad, item.total)) + colorama.Style.RESET_ALL)
		
		print(item.get_solution())
		print()
			
		if item.main_l2 is not None:
			if not args.no_audio:
				audio.play_audio(item.main_l2, dl, args.target)
	
	trainer = VocTrainer(vocabulary, on_prompt, on_input, on_solution)
	while True:
		print()
		print(
			colorama.Fore.BLUE + colorama.Style.BRIGHT +
			"New round!" +
			colorama.Style.RESET_ALL
		)
		print()
		if not trainer.start_round():
			break
	
	print_summary(trainer.vocabulary)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--source", action="store", default="de", help="source language")
	parser.add_argument("--target", action="store", default="fr", help="target language")
	parser.add_argument("--t2s", action="store_true", help="translate target to source")
	parser.add_argument("--debug", action="store_true", help="enable debug output")
	parser.add_argument("--no-audio", action="store_true", help="disable audio output")
	args = parser.parse_args()

	main(args)
