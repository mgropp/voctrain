#!/usr/bin/env python3
import argparse
import duolingo
import colorama
import signal

from auth import user, password
from voctrain import VocTrainer
import audio

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


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--source", action="store", default="de", help="source language")
	parser.add_argument("--target", action="store", default="fr", help="target language")
	parser.add_argument("--t2s", action="store_true", help="translate target to source")
	args = parser.parse_args()
	
	dl = duolingo.Duolingo(user, password)
	
	skills = dl.get_learned_skills(args.target)
	print(skills[0].keys())
	skills = sorted(skills, key=lambda x: (int(x["coords_y"]), int(x["coords_x"])))
	print(skills[12])
	
	print(colorama.Fore.WHITE + colorama.Style.BRIGHT + "Choose a skill!" + colorama.Style.RESET_ALL)
	for n, s in zip(range(1, len(skills)+1), skills):
		print("%2s) %s (%.2f)" % (n, s["title"], s["strength"]))
	
	while True:
		try:
			skill_index = input(colorama.Fore.YELLOW + ">>> " + colorama.Style.RESET_ALL)
		except EOFError:
			print()
			return False
		
		try:
			skill_index = int(skill_index.strip())
		except:
			continue
		
		if 1 <= skill_index <= len(skills):
			skill = skills[skill_index - 1]
			break
	
	words = get_words(skill["title"], dl.get_vocabulary(args.target)["vocab_overview"])
	translations_t2s = dl.get_translations(
		words,
		source=args.source,
		target=args.target
	)
	
	if args.t2s:
		translations = translations_t2s
		vocabulary = [ ([x], y, x, None, "%s -> %s" % (x, ", ".join(y))) for x, y in translations.items() ]
	else:
		translations_s2t = dl.get_translations(
			list(set(( x for sl in translations_t2s.values() for x in sl  ))),
			source=args.target,
			target=args.source
		)
		
		print(translations_t2s)
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
		
	
	def on_prompt(item):
		if item.main_l1 is not None:
			audio.play_audio(item.main_l1, dl, args.target)
	
	def on_solution(item, answer, correct):
		if item.main_l2 is not None:
			audio.play_audio(item.main_l2, dl, args.target)
	
	if len(vocabulary) == 0:
		print("No words found!")
	
	else:
		trainer = VocTrainer(vocabulary, on_prompt=on_prompt, on_solution=on_solution)
		while True:
			print()
			print(colorama.Fore.BLUE + colorama.Style.BRIGHT + "New round!" + colorama.Style.RESET_ALL)
			print()
			if not trainer.start_round():
				break
		
		print()
		print(colorama.Fore.BLUE + colorama.Style.BRIGHT + "Summary" + colorama.Style.RESET_ALL)
		trainer.print_summary()


if __name__ == "__main__":
	main()
