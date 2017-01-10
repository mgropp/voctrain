#!/usr/bin/env python3
import duolingo
import argparse
from collections import namedtuple

from auth import user, password

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--translate", action="store_true", help="include translations")
	parser.add_argument("--source", action="store", default="de", help="source language")
	parser.add_argument("--target", action="store", default="fr", help="target language")
	parser.add_argument("--all", action="store_true", help="list words from all lessons")
	args = parser.parse_args()
	
	dl = duolingo.Duolingo(user, password)
	voc = dl.get_vocabulary(args.target)

	VocItem = namedtuple("VocItem", voc["vocab_overview"][0].keys())
	words = [ VocItem(**x) for x in voc["vocab_overview"] ]
	
	if not args.all:
		from duovoctrain import get_all_skills, choose_skill
		skills = [ s for s in get_all_skills(dl, args.target) if float(s["progress_percent"]) > 0 ]
		skill = choose_skill(skills)
		words = [ v for v in words if v.skill == skill["title"] ]
	
	words = sorted(words, key=lambda x: (x.strength, -x.last_practiced_ms))
	
	if args.translate:
		translations = dl.get_translations(
			[ x.word_string for x in words ],
			source=args.source,
			target=args.target
		)
	else:
		translations = dict()
	
	for word in words:
		note = ""
		if hasattr(word, "gender") and word.gender is not None:
			note = " (%s)" % word.gender
		elif hasattr(word, "infinitive") and word.infinitive is not None:
			note = " (%s)" % word.infinitive
		
		translation = translations.get(word.word_string, "")
		if len(translation) > 0:
			translation = ": %s" % ", ".join(translation)
		
		print("%4s %s%s%s" % ("*" * word.strength_bars, word.word_string, note, translation))
