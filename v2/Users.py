import json
import time
import glob
from AnimeScraper import user_scrape, Scrape
from searcher import find_by_id
import searcher
from collections import defaultdict
import itertools
from functools import lru_cache

from multiprocessing.dummy import Pool

def add_new_anime(ID):
	if searcher.find_by_id(ID) != None:
		print("Already have {} in the system!".format(ID))
		return None
	anime = AnimeScraper.Scrape(ID)
	return anime

p = Pool(8)

check_1 = []
check_2 = []
check_3 = []
check_4 = []
check_5 = []

class User:
	def __init__(self, username):
		self.username = username
		self.file_name = "Users/{}.json".format(username)
		self.user_data = user_scrape(self.username)
		self.IDs = [x['anime_id'] for x in self.user_data]
		self.complete_IDs = [x['anime_id'] for x in self.user_data if str(x['status']) in ['1', '2']]

		self.average_difference = [x['score']/find_by_id(x['anime_id'])['score'] for x in self.user_data if x != None and find_by_id(x['anime_id']) != None and x['score'] != 0]
		self.average_difference = sum(self.average_difference)/len(self.average_difference)
		print(round(self.average_difference, 2))

		self.recommendations = None

		self.confirm_valid()

	def confirm_valid(self):
		refresh_animes = []
		for anime in self.user_data:
			if find_by_id(anime['anime_id']) == None:
				refresh_animes.append(Scrape(anime['anime_id']))

		refresh_animes = [x for x in refresh_animes if x != None]
		if len(refresh_animes) != 0:
			searcher.refresh(refresh_animes)


	# Loads data from a json file to recreate this object
	def load(self):
		with open(self.file_name) as f:
			self.json_data = json.load(f)
		return self

	def dump(self):
		with open(self.file_name, 'w') as f:
			json.dump(self.json_data, f, indent = 2)
		return self

	def generate(self):
		json_data = {}
		json_data['raw_genres'] = defaultdict(list)
		json_data['normalized_genres'] = defaultdict(list)
		json_data['normalized_studio'] = defaultdict(list)
		json_data['normalized_staff'] = defaultdict(list)
		for anime in self.user_data:
			score = anime['score']
			if score == 0:
				continue
			status = anime['status']
			mal_id = anime['anime_id']
			# print(type(mal_id))
			anime = find_by_id(mal_id)
			if anime == None:
				print(mal_id)
				continue
			# print(anime)
			for genre in anime['genre']:
				json_data['raw_genres'][genre['name']].append(score)
				json_data['normalized_genres'][genre['name']].append(round(score/anime['score'], 2))

			# input()
		self.json_data = json_data
		return self

	# @lru_cache(maxsize = 100)
	#
	# def time_print(self):
	# 	global check_1, check_2, check_3, check_4, check_5
	# 	print("Check 1: {}".format(sum(check_1)/len(check_1)))
	# 	print("Check 2: {}".format(sum(check_2)/len(check_2)))
	# 	print("Check 3: {}".format(sum(check_3)/len(check_3)))
	# 	print("Check 4: {}".format(sum(check_4)/len(check_4)))
	# 	print("Check 5: {}, {}".format(sum(check_5)/len(check_5), sum(check_5)))
	# 	check_1 = []
	# 	check_2 = []
	# 	check_3 = []
	# 	check_4 = []
	# 	check_5 = []

	def calculate_combos(self):
		combos = set()
		for anime in self.user_data:
			score = anime['score']
			if score == 0:
				continue
			status = anime['status']
			mal_id = anime['anime_id']
			# print(mal_id)
			anime = find_by_id(mal_id)
			if anime == None:
				continue

			# GENRES
			genres = [x['name'] for x in anime['genre'] if x != None]
			for genre_group in [combo for x in range(1, len(genres)+1) for combo in itertools.combinations(genres, x)]:
				str_genre_group = str("|".join(sorted(genre_group)))
				self.json_data['normalized_genres'][str_genre_group] = self.json_data['normalized_genres'].get(str_genre_group, []) + [round(score/anime['score'], 2)]


			# STUDIO
			studios = [x['name'] for x in anime['studio']]
			licensors = [x['name'] for x in anime['licensor']]
			producers = [x['name'] for x in anime['producer']]
			All = studios + licensors + producers
			for studio in All:
				self.json_data['normalized_studio'][studio] = self.json_data['normalized_studio'].get(studio, []) + [round(score/anime['score'], 2)]

			# STAFF
			staff = [x['name'] for x in anime.get('staff', [])]
			for s in staff:
				self.json_data['normalized_staff'][s] = self.json_data['normalized_staff'].get(s, []) + [round(score/anime['score'], 2)]


		# print(len(combos))

	def genre_rating(self, genres):

		ratings = []
		if type(genres) != list:
			genres = [genres]

		for genre_group in [combo for x in range(1, min(len(genres)+1, 5)) for combo in itertools.combinations(genres, x)]:
			str_genre_group = str("|".join(sorted(genre_group)))
			sub_ratings = self.json_data['normalized_genres'].get(str_genre_group, [1])
			ratings += [sum(sub_ratings)/len(sub_ratings) * (1/self.average_difference)] * len(genre_group)
		res = sum(ratings + ([1] * 1))/len(ratings + ([1] * 1))

		# print(res)
		return res

	# @lru_cache(maxsize = 100)
	def studio_rating(self, passed_anime):
		ratings = []
		studios = [x['name'] for x in passed_anime['studio']]
		licensors = [x['name'] for x in passed_anime['licensor']]
		producers = [x['name'] for x in passed_anime['producer']]
		All = studios + licensors + producers
		for studio in All:
			sub_ratings =  self.json_data['normalized_studio'].get(studio, [1])
			ratings += [sum(sub_ratings)/len(sub_ratings) * (1/self.average_difference)]
		return sum(ratings + ([1] * 2))/len(ratings + ([1] * 2))


	def staff_rating(self, passed_anime):
		if passed_anime.get('staff') == None:
			return 1
		ratings = []
		staff = [x['name'] for x in passed_anime.get('staff', [])]
		for s in staff:
			sub_ratings = self.json_data['normalized_staff'].get(s, [1]) #get_rating_for(s)
			ratings += [sum(sub_ratings)/len(sub_ratings) * (1/self.average_difference)]
		return sum(ratings + ([1] * 1))/len(ratings + ([1] * 1))

	# @lru_cache(maxsize = 100)
	def watch_prequel(self, anime):
		# print(anime['mal_id'])
		prequels = anime['related']['Prequel']
		for pre in prequels:
			if pre['mal_id'] in self.complete_IDs:
				return True
		# print("Not Watched Prequel of {}".format(anime))
		return False

	def __getattr__(self, name):
		out = self.json_data.get(name, None)
		if out:
			return out
		else:
			raise KeyError(name)

USERS = {}
def find_user_object(username):
	if username in USERS:
		return USERS[username]
	USER = None
	file_name = "Users/{}.json".format(username)
	for found_file in glob.glob('Users/*.json'):
		if file_name == found_file.replace("\\", '/'):
			USER = User(username).load()
	if USER == None:
		USER = User(username).generate()
	USERS[username] = USER
	USER.calculate_combos()
	return USER
