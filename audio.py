import os
import os.path
import urllib
import urllib.request

cache_base_dir = os.path.join(os.path.expanduser("~"), ".cache", "duovoc")

def get_audio_file(word, duolingo, language, cache=True):
	word = urllib.parse.quote_plus(word)
	
	cache_dir = os.path.join(cache_base_dir, language)
	if not os.path.exists(cache_dir):
		os.makedirs(cache_dir)
	
	filename = os.path.join(cache_dir, word)
	
	if os.path.exists(filename):
		return filename
	
	url = duolingo.get_audio_url(word, language_abbr=language, random=False)
	urllib.request.urlretrieve(url, filename)
	
	return filename


def play_audio_dummy(word, duolingo, language):
	pass


_pygame_initialized = False

def play_audio_pygame(word, duolingo, language, wait=False):
	import pygame
	
	filename = get_audio_file(word, duolingo, language)
	
	global _pygame_initialized
	if not _pygame_initialized:
		print("*Initializing pygame*")
		pygame.init()
		pygame.mixer.init()
		_pygame_initialized = True
	
	pygame.mixer.music.load(filename)
	pygame.mixer.music.play()
	
	if wait:
		while pygame.mixer.music.get_busy():
			pygame.time.Clock().tick(10)


def is_supported_pygame():
	try:
		import pygame
		return True
	except:
		return False


_pool = None

def play_audio_mpg123(word, duolingo, language):
	import concurrent.futures
	import subprocess
	
	filename = get_audio_file(word, duolingo, language)
	
	# we should probably join the thread at some point, but...
	global _pool
	if _pool is None:
		_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
	
	_pool.submit(lambda: subprocess.run([ "mpg123", filename ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))


def is_supported_mpg123():
	try:
		import subprocess
		subprocess.check_call([ "mpg123", "--help" ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		return True
	except:
		return False


play_audio = play_audio_dummy
if is_supported_mpg123():
	play_audio = play_audio_mpg123
elif is_supported_pygame():
	play_audio = play_audio_pygame
