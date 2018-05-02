import json
from functools import lru_cache
from datetime import datetime
import math
from multiprocessing.dummy import Pool
from threading import Thread, Lock

def index_database(database, **kwargs):
	db = {}
	p = Pool(kwargs.get("pools", 20))
	def process(entry):
		if entry == None:
			return
		db[entry['mal_id']] = entry
	p.map(process, database)
	return db

try:
	with open("INDEXED_DATABASE.json") as f:
		INDEXED_DATABASE = json.load(f)
	# print(INDEXED_DATABASE.keys())
except:
	with open("DATABASE.json") as f:
		INDEXED_DATABASE = index_database(json.load(f))

FILE_LOCK = Lock()

def write():
	with FILE_LOCK:
		print("Writing to File")
		with open("INDEXED_DATABASE.json", 'w') as f:
			json.dump(INDEXED_DATABASE, f, indent = 2)	

def refresh(animes):
	print("Refreshing Database file")
	for anime in animes:
		if anime != None:
			INDEXED_DATABASE[str(anime['mal_id'])] = anime
	t = Thread(target = write, name = "Anime Database Writer")
	t.start()


# @lru_cache(maxsize = 1000)
def find_by_id(mal_id):
	return INDEXED_DATABASE.get(str(mal_id))

def find_kwargs(**kwargs):
	ret = []
	p = Pool(kwargs.get("pools", 10))

	def process(entry):
		if entry != None and resolve_kwargs(entry, kwargs):
			return entry

	a = p.map(process, INDEXED_DATABASE.values())

	return [x for x in a if x != None]

def resolve_kwargs(entry, kwargs):
	try:
		for kwarg in kwargs:
			if kwarg == 'before_date':
				# If the start aired date is after the given date
				if entry['aired'].get('from', '9999') > str(kwargs[kwarg]) and entry['aired'].get('on', '9999') > str(kwargs[kwarg]):
					return False
			elif kwarg == 'after_date':
				# If the ending aired date is before the given date
				if entry['aired'].get('from', '0000') < str(kwargs[kwarg]) and entry['aired'].get('on', '0000') < str(kwargs[kwarg]):
					return False
			elif kwarg == 'score_above':
				# If the score is below
				if entry['score'] < kwargs[kwarg]:
					return False
			elif kwarg == 'produced_by':
				if kwargs[kwarg].lower() not in [x['name'].lower() for x in entry['producer']]:
					return False

			elif kwarg == 'include_genres':
				entry_genres = [g['name'].lower() for g in entry['genre']]
				for genre in kwargs[kwarg]:
					if genre.lower() not in entry_genres:
						return False

			elif kwarg == 'exclude_genres':
				entry_genres = [g['name'].lower() for g in entry['genre']]
				for genre in kwargs[kwarg]:
					if genre.lower() in entry_genres:
						return False

			elif kwarg == 'less_eps':
				if entry['episodes'] > kwargs[kwarg]:
					return False

			elif entry[kwarg] != kwargs[kwarg]:
				return False
	except:
		print("We broke it")
		pass
		# print(entry)
	return True

def find_MAL_recs(mal_id):
	pass

