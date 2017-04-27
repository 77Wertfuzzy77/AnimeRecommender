import json
import xmltodict
import requests
from bs4 import BeautifulSoup
from threading import Thread
import threading
import time
import math
import sys
import itertools
import random

class Analyzer:
	def __init__(self, ** kwargs):
		self.FileName = kwargs.get('name')
		self.ANIME_TO_GENRES = {}
		self.RETRIES = kwargs.get('retries', 10)
		self.CUTOFF_PERCENT = kwargs.get("cutoff", 0.08)
		self.TYPES = [x.upper() for x in kwargs.get('types', ["TV"])]
		self.STATUS =  [x.upper() for x in kwargs.get('status', ['DROPPED', 'COMPLETED', 'PLAN TO WATCH', 'WATCHING', 'ON-HOLD'])]
		self.GenresByRating = {}
		self.COUNT = 0
		self.RATINGSLIST = []

		with open("{}.xml".format(self.FileName), 'rb') as f:
			parsed = xmltodict.parse(f)
			JSON = json.loads(json.dumps(parsed))['myanimelist']

		with open("Genres.json", 'r') as f:
			self.ID_TO_GENRES = json.load(f)

		self.ANIMES = JSON['anime']
		self.INFO = JSON['myinfo']

	def getGenres(self, anime):
		if anime['my_status'].upper() not in self.STATUS or anime['series_type'].upper() not in self.TYPES:
			return self
		if int(anime['my_score']) == 0:
			return self

		self.RATINGSLIST.append(int(anime['my_score']))

		# If we have discovered this anime before
		if anime['series_animedb_id'] in self.ID_TO_GENRES.keys():
			self.ANIME_TO_GENRES[json.dumps(anime)] = self.ID_TO_GENRES[anime['series_animedb_id']]['Genres']
			self.ID_TO_GENRES[anime['series_animedb_id']]['Ratings'][self.INFO['user_id']] = int(anime['my_score'])
			self.COUNT += 1
			return self

		# Try to get Site information
		site = requests.get("https://myanimelist.net/anime/"+ anime['series_animedb_id'])
		retries = 0
		while site.status_code != 200 and retries <= self.RETRIES:
			time.sleep(5)
			site = requests.get("https://myanimelist.net/anime/"+ anime['series_animedb_id'])
			retries += 1

		# If we retried too much
		if retries == self.RETRIES + 1:
			return self

		# Us Beautiful Soup to pull the Genres from the page
		soup = BeautifulSoup(site.text, "html.parser")
		rawGenres = soup.find('span', text='Genres:')
		Genres = [x.text for x in rawGenres.parent.find_all(href = True)]

		self.ANIME_TO_GENRES[json.dumps(anime)] = Genres
		self.ID_TO_GENRES[anime['series_animedb_id']] = {
		'Genres' : Genres,
		'Ratings' : {self.INFO['user_id'] : int(anime['my_score'])},
		'Title' : anime['series_title'],
		'Type' : anime['series_type'] 
		}
		self.COUNT += 1
		print("Found a new Anime! ({})".format(anime['series_title']))
		return self

	def runThreads(self):
		queue = []
		for anime in self.ANIMES:
			thr = Thread(target = self.getGenres, args = [anime])
			queue.append(thr)
		while len(queue) > 0:
			while threading.activeCount() <= 10 and len(queue) > 0:
				queue.pop().start()

		while(threading.activeCount() > 1):
			print("Waiting for finish... ({} remaining)".format(threading.activeCount() - 1))
			time.sleep(3)
		return self

	def aggregate(self):
		self.LOWESTRATING = sorted(self.RATINGSLIST)[:1][0]
		self.HIGHESTRATING = sorted(self.RATINGSLIST, reverse=True)[:1][0]

		for anime, genres in self.ANIME_TO_GENRES.items():
			anime = json.loads(anime)
			for genre in genres:
				if genre in self.GenresByRating.keys():
					self.GenresByRating[genre].append(int(anime['my_score']))
				else:
					self.GenresByRating[genre] = [int(anime['my_score'])]

			pairs = [combo for L in range(0, len(genres)+1) for combo in itertools.combinations(genres, L)][1:]
			for pair in pairs:
				pair = sorted(pair)
				Combo = "/".join(pair)
				if Combo in self.GenresByRating.keys():
					self.GenresByRating[Combo].append(int(anime['my_score']))
				else:
					self.GenresByRating[Combo] = [int(anime['my_score'])]


		items = self.GenresByRating.items()
		for genre, ratings in items:
			self.GenresByRating[genre] = {
			'average' : round(sum(ratings) / len(ratings), 2),
			'ratings' : ratings,
			'score' : round((sum(ratings) / len(ratings) - self.LOWESTRATING) / (self.HIGHESTRATING - self.LOWESTRATING), 3),
			'single' : "/" not in genre,
			'display' : len(ratings) > self.COUNT * self.CUTOFF_PERCENT
			}

		self.TOP5 = sorted(self.GenresByRating.items(), key = lambda x: x[1]['score'] if x[1]['single'] and x[1]['display'] else 0, reverse = True)[:5]
		return self

	def writeAnalysisToFile(self):
		sorted_genres = sorted(self.GenresByRating.items(), key=lambda t: t[1]['score'], reverse = True)
		output = "Username: {}\nID: {}\nAnimes Analyzed: {}\nCut-off: {}%\nTypes: {}\nStatus: {}\n\n".format(self.INFO['user_name'], self.INFO['user_id'], self.COUNT, round(self.CUTOFF_PERCENT * 100, 1), ", ".join(self.TYPES), ", ".join(self.STATUS))
		for single in sorted_genres:
			d = single[1]
			if d['display'] and d['single']:
				output += "{:16s}Score: {:5s} Average: {:5s} Num Watched: {:5s}\n".format(single[0], str(d['score']), str(d['average']), str(len(d['ratings'])))
				First = True 
				Split = False
				for subGenre in sorted_genres:
					if single[0] in subGenre[0] and not subGenre[1]['single'] and subGenre[1]['display']:
						if subGenre[1]['score'] < single[1]['score'] and not First and not Split:
							Split = True
							output += "-"*80 + "\n"
						catagory = subGenre[0].split("/")
						try:
							catagory.remove(single[0])
						except:
							pass
						Symbol = "+" if not Split else "-"
						output += "{} {:35s}Score: {:5s} Average: {:5s} Num Watched: {:5s}\n".format(Symbol, "/".join(catagory), str(subGenre[1]['score']), str(subGenre[1]['average']), str(len(subGenre[1]['ratings'])))
					First = False
				output += "\n"

		with open("Output\{}.txt".format(self.FileName), 'w') as f:
			f.write(output)
		return self

	def updateDatabase(self):
		with open("Genres.json", 'w') as f:
			json.dump(self.ID_TO_GENRES, f, indent = 4)
		return self

def CreateFile(name, ** kwargs):
	kwargs['name'] = name
	A = Analyzer(** kwargs)
	A.runThreads().aggregate().writeAnalysisToFile().updateDatabase()
	print("Output file named: '{}.txt'".format(kwargs.get('name')))
	return A

def WillILike(name, genres, **kwargs):
	kwargs['name'] = name
	A = Analyzer(** kwargs)
	A.runThreads().aggregate()
	pairs = [combo for L in range(0, min(len(genres)+1, 5)) for combo in itertools.combinations(genres, L)][1:]
	Scores = []
	for pair in pairs:
		pair = sorted(pair)
		try:
			info = A.GenresByRating["/".join(pair)]
			if info['score'] == 0:
				continue
			for x in range(len(pair)+1):
				Scores.append(info['score'])
			if not kwargs.get('quiet', False):
				print("{} - {}".format("/".join(pair), info['score']))
		except:
			if not kwargs.get('quiet', False):
				print("Not found combo of {}".format("/".join(pair)))

	if not kwargs.get('quiet', False):
		print("Your top Animes with this pairing")
		GoodAnimes = []
		for anime, animegenres in A.ANIME_TO_GENRES.items():
			anime = json.loads(anime)
			ContainsAll = len([True for genre in genres if genre in animegenres]) == len(genres)
			if ContainsAll:
				GoodAnimes.append((anime['series_title'], anime['my_score']))

		top5 = ["{} - {}".format(anime[0], anime[1]) for anime in sorted(GoodAnimes, key = lambda x: x[1], reverse = True)[:5]]
		print("\n".join(top5))

	return round(sum(Scores)/len(Scores), 3)

def recommendGenreGroups(name, num, **kwargs):
	kwargs['name'] = name
	A = Analyzer(** kwargs)
	A.runThreads().aggregate().updateDatabase()
	single_genres = [genre[0] for genre in A.GenresByRating.items() if genre[1]['single'] and genre[1]['display']]
	groupings = [combo for x in range(3, 6, 1) for combo in itertools.combinations(single_genres, x)]
	Entries = {}
	for genres in groupings:
		if "/".join(genres) in A.GenresByRating.keys() and kwargs.get('new_groups', False):
			continue
		if "/".join(genres) not in A.GenresByRating.keys() and kwargs.get('current_groups', False):
			continue
		pairs = [combo for L in range(0, min(len(genres)+1, kwargs.get("largest_group_size", 5))) for combo in itertools.combinations(genres, L)][1:]
		Scores = []
		for pair in pairs:
			pair = sorted(pair)
			try:
				info = A.GenresByRating["/".join(pair)]
				if info['score'] == 0:
					continue
				for x in range(len(pair)+1):
					Scores.append(info['score'])
			except:
				pass

		Entries["/".join(pair)] = round(sum(Scores)/len(Scores), 3) if len(Scores) > 0 else 0
	return sorted(Entries.items(), key = lambda x: x[1], reverse = True)[:num]
	#group_to_rating = [(group, WillILike("Nikolai", group, quiet = True)) for group in groupings]

def recommendAnimes(name, num, **kwargs):
	A = Analyzer(name=name,** kwargs)
	A.runThreads().aggregate().updateDatabase()
	goodGenres = recommendGenreGroups(name, kwargs.get("sample_pool", 10), **kwargs)
	runs = 0
	retList = []
	for genreGroup in goodGenres:
		GoodAnimes = FindInDataBase(genreGroup[0].split('/'))
		for anime in GoodAnimes:
			if A.INFO['user_id'] not in anime[1]['Ratings'].keys() and anime[1]['Title'] not in [x[0] for x in retList]:
				retList.append((anime[1]['Title'], round(WillILike(name, anime[1]['Genres'], quiet = True, **kwargs) * sum(anime[1]['Ratings'].values()) / len(anime[1]['Ratings']), 3)))
	sortedList = sorted(retList, key = lambda x: x[1], reverse = True)
	return sortedList[:num]

def FindInDataBase(genreGroup):
	with open("Genres.json", 'r') as f:
		ID_TO_GENRES = json.load(f)
	toRet = []
	for entry in ID_TO_GENRES.items():
		if set(entry[1]['Genres']) >= set(genreGroup):
			toRet.append(entry)
	return toRet

def TopX(name, num, **kwargs):
	kwargs['name'] = name
	A = Analyzer(** kwargs)
	A.runThreads().aggregate().updateDatabase()
	return sorted(A.GenresByRating.items(), key = lambda x: x[1]['score'] if x[1]['single'] and x[1]['display'] else 0, reverse = True)[:num]

def AnimeCompare(name1, name2, ** kwargs):
	kwargs['name'] = name1
	FirstA = Analyzer(** kwargs).runThreads().aggregate()
	kwargs['name'] = name2
	SecondA = Analyzer(** kwargs).runThreads().aggregate()
	toPrint = ""
	sorted1 = sorted(FirstA.GenresByRating.items(), key=lambda t: t[1]['score'], reverse = True)
	sorted2 = sorted(SecondA.GenresByRating.items(), key=lambda t: t[1]['score'], reverse = True)

	for genre1 in sorted1:
		d = genre1[1]

		if len(d['ratings']) > FirstA.COUNT * FirstA.CUTOFF_PERCENT and d['single'] and genre1[0] in [x[0] for x in sorted2] and SecondA.GenresByRating[genre1[0]]['score'] != 0:
			FirstScoreSingle = str(FirstA.GenresByRating[genre1[0]]['score'])
			SecondScoreSingle = SecondA.GenresByRating[genre1[0]]['score']

			toPrint += "{:17s} {}'s Score: {:5s} {}'s Score: {}\n".format(genre1[0], name1, FirstScoreSingle, name2, SecondScoreSingle)

			for double in sorted1:

				if genre1[0] in double[0] and not double[1]['single'] and double[1]['score'] != 0 and double[0] in [x[0] for x in sorted2] and SecondA.GenresByRating[double[0]]['score'] != 0:
					catagory = double[0].split("/")
					try:
						catagory.remove(genre1[0])
					except:
						pass

					FirstScoreDouble = str(FirstA.GenresByRating[double[0]]['score'])
					SecondScoreDouble = SecondA.GenresByRating[double[0]]['score']
					toPrint += "- {:15s} {}'s Score: {:5s} {}'s Score: {}\n".format(catagory[0], name1, FirstScoreDouble, name2, SecondScoreDouble)
			toPrint += "\n"
	print("File Output at '{}&{}.txt'".format(name1, name2))
	with open("Output\{}&{}.txt".format(name1, name2), 'w') as f:
		f.write(toPrint)
	return FirstA, SecondA
