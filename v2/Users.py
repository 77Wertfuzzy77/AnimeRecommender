import json
import time
import glob
from AnimeScraper import user_scrape, Scrape
from searcher import find_by_id
import searcher
from collections import defaultdict
import itertools
from functools import lru_cache

def add_new_anime(ID):
	if searcher.find_by_id(ID) != None:
		print("Already have {} in the system!".format(ID))
		return None
	anime = AnimeScraper.Scrape(ID)	
	return anime

class User:
	def __init__(self, username):
		self.username = username
		self.file_name = "Users/{}.json".format(username)
		self.user_data = user_scrape(self.username)
		self.IDs = [x['anime_id'] for x in self.user_data]
		self.complete_IDs = [x['anime_id'] for x in self.user_data if str(x['status']) in ['1', '2']]

		self.average_difference = [x['score']/find_by_id(x['anime_id'])['score'] for x in self.user_data if x != None and find_by_id(x['anime_id']) != None and x['score'] != 0]
		self.average_difference = sum(self.average_difference)/len(self.average_difference)
		print(self.average_difference)


		self.recommendations = None

		self.genre_ratings = {}
		self.studio_ratings = {}
		self.staff_ratings = {}

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
	def genre_rating(self, genres):

		if type(genres) != list:
			comp = [genres]
		else:
			comp = genres
		comp = str("|".join(sorted(comp)))
		if comp in self.genre_ratings:
			return self.genre_ratings[comp]

		def get_rating_for(genre_group, dict_name):

			if len(genre_group) == 1:
				genre_group = genre_group[0]
			else:
				genre_group = str("|".join(sorted(genre_group)))

			if genre_group in self.json_data[dict_name].keys():
				# print("Found stored value {}".format(genre_group))
				return self.json_data[dict_name][genre_group]
			# print(genre_group)
			set_genre_group = set(genre_group.split("|"))

			for anime in self.user_data:
				score = anime['score']
				if score == 0:
					continue
				status = anime['status']
				mal_id = anime['anime_id']
				# print(mal_id)
				anime = find_by_id(mal_id)
				if anime == None:
					return [1]

				if set_genre_group <= set([x['name'] for x in anime['genre'] if x != None]):
					if dict_name == 'normalized_genres':
						self.json_data['normalized_genres'][genre_group] = self.json_data['normalized_genres'].get(genre_group, []) + [round(score/anime['score'], 2)]
					else:
						raise Error("Bad Dictionary Name")
			if genre_group in self.json_data[dict_name].keys():
				return self.json_data[dict_name][genre_group]
			else:
				return [1]

		ratings = []
		if type(genres) != list:
			genres = [genres]
		# print(genres)
		for genre_group in [combo for x in range(1, len(genres)+1) for combo in itertools.combinations(genres, x)]:
			# print(genre_group)
			sub_ratings = get_rating_for(genre_group, 'normalized_genres')
			if len(sub_ratings) == 0:
				continue
			ratings += [sum(sub_ratings)/len(sub_ratings) * (1/self.average_difference)]# * len(genre_group)

		res = sum(ratings + ([1] * 1))/len(ratings + ([1] * 1))
		self.genre_ratings[comp] = res 
		return res 

	# @lru_cache(maxsize = 100)
	def studio_rating(self, passed_anime):
		def get_rating_for(studio):
			if studio in self.json_data['normalized_studio'].keys():
				return self.json_data['normalized_studio'][studio]

			for anime in self.user_data:
				score = anime['score']
				if score == 0:
					continue
				status = anime['status']
				mal_id = anime['anime_id']
				anime = find_by_id(mal_id)
				if anime == None:
					return [1]

				studios = [x['name'] for x in anime['studio']]
				licensors = [x['name'] for x in anime['licensor']]
				producers = [x['name'] for x in anime['producer']]

				if studio in studios or studio in licensors or studio in producers:
					self.json_data['normalized_studio'][studio] = self.json_data['normalized_studio'].get(studio, []) + [round(score/anime['score'], 2)]

			if studio in self.json_data['normalized_studio'].keys():
				return self.json_data['normalized_studio'][studio]
			else:
				return [1]

		ratings = []
		studios = [x['name'] for x in passed_anime['studio']]
		licensors = [x['name'] for x in passed_anime['licensor']]
		producers = [x['name'] for x in passed_anime['producer']]
		All = studios + licensors + producers

		for studio in All:
			sub_ratings = get_rating_for(studio)
			if len(sub_ratings) == 0:
				continue
			ratings += [sum(sub_ratings)/len(sub_ratings) * (1/self.average_difference)]
		return sum(ratings + ([1] * 2))/len(ratings + ([1] * 2))


	def staff_rating(self, passed_anime):
		if passed_anime.get('staff') == None:
			return 1
		def get_rating_for(staff):
			if staff in self.json_data['normalized_staff'].keys():
				return self.json_data['normalized_staff'][staff]

			for anime in self.user_data:
				score = anime['score']
				if score == 0:
					continue
				status = anime['status']
				mal_id = anime['anime_id']
				anime = find_by_id(mal_id)
				if anime == None:
					return [1]

				if anime.get('staff') == None:
					return [1]

				all_staff = [x['name'] for x in anime['staff']]

				if staff in all_staff:
					self.json_data['normalized_staff'][staff] = self.json_data['normalized_staff'].get(staff, []) + [round(score/anime['score'], 2)]

			if staff in self.json_data['normalized_staff'].keys():
				return self.json_data['normalized_staff'][staff]
			else:
				return [1]

		ratings = []
		staff = [x['name'] for x in passed_anime.get('staff', [])]
		for s in staff:
			sub_ratings = get_rating_for(s)
			if len(sub_ratings) == 0:
				continue
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
	return USER