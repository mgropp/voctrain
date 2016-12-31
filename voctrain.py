#!/usr/bin/env python3
from collections import namedtuple
import random
import colorama
from unidecode import unidecode

class VocItem(object):
	def __init__(self, l1, l2, main_l1, main_l2, solution=None, ignore_case=True, ignore_accents=True):
		self.bad = 0
		self.total = 0
		self.ignore_case = ignore_case
		self.ignore_accents = ignore_accents
		self.solution = solution
		
		self.l1 = l1
		self.l2 = l2
		self.main_l1 = main_l1
		self.main_l2 = main_l2
		
		self.ref_l2 = l2
		if ignore_case:
			self.ref_l2 = [ x.lower() for x in self.ref_l2 ]
		if ignore_accents:
			self.ref_l2 = [ unidecode(x) for x in self.ref_l2 ]
	
	
	def __repr__(self):
		return "%s -> %s (%s/%s)" % (self.l1, self.l2, self.bad, self.total)
	
	
	def get_prompt(self):
		return ", ".join(self.l1)
	
	
	def get_solution(self, play_audio=True):
		if self.solution is None:
			return ", ".join(self.l2)
		else:
			return "%s\n(%s)" % (self.solution, ", ".join(self.l2))
	
	
	def check(self, answer):
		answer = answer.strip()
		if self.ignore_case:
			answer = answer.lower()
		if self.ignore_accents:
			answer = unidecode(answer)
		
		self.total += 1
		if answer in self.ref_l2:
			return True
		else:
			self.bad += 1
			return False


class VocTrainer(object):
	def __init__(self, vocabulary, ignore_case=True, ignore_accents=True, on_prompt=None, on_solution=None):
		"""
		vocabulary: [([source], [target])]
		"""
		
		self.on_prompt = on_prompt
		self.on_solution = on_solution
		
		self.vocabulary = list()
		for voc in vocabulary:
			if len(voc) == 4:
				l1, l2, main_l1, main_l2 = voc
				solution = None
			else:
				l1, l2, main_l1, main_l2, solution = voc
			
			self.vocabulary.append(VocItem(l1, l2, main_l1, main_l2, solution, ignore_case, ignore_accents))
	
	
	def start_round(self):
		items = self.vocabulary[:]
		random.shuffle(items)
		items = sorted(items, key=lambda x: x.bad)
		
		while True:
			todo = []
			i = 0
			while i < len(items):
				item = items[i]
				
				print(colorama.Fore.WHITE + colorama.Style.BRIGHT + item.get_prompt() + colorama.Style.RESET_ALL)
				if self.on_prompt is not None:
					self.on_prompt(item)
				
				try:
					answer = input(colorama.Fore.YELLOW + ">>> " + colorama.Style.RESET_ALL)
				except EOFError:
					print()
					return False
				
				correct = item.check(answer)
				if correct:
					print(colorama.Fore.GREEN + ("Correct! (%d/%d)" % (item.total - item.bad, item.total)) + colorama.Style.RESET_ALL)
				else:
					print(colorama.Fore.RED + ("Wrong! (%d/%d)" % (item.total - item.bad, item.total)) + colorama.Style.RESET_ALL)
					pos = i + min(random.randint(3, 4), len(items))
					items.insert(pos, item)
					todo.append(item)
				
				print(item.get_solution())
				print()
				
				if self.on_solution is not None:
					self.on_solution(item, answer, correct)
				
				i += 1
			
			if len(todo) == 0:
				break
			
			items = todo
			random.shuffle(items)
		
		return True
	
	
	def print_summary(self):
		v = [ x for x in self.vocabulary if x.bad > 0 ]
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


if __name__ == "__main__":
	vocabulary = [
		(["test"], [ "test", "test" ]),
		(["test2"], [ "test2", "test2" ])
	]
	
	trainer = VocTrainer(vocabulary)
	while True:
		print()
		print(colorama.Fore.BLUE + colorama.Style.BRIGHT + "New round!" + colorama.Style.RESET_ALL)
		print()
		if not trainer.start_round():
			break
