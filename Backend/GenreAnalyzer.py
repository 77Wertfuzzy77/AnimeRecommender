import json
import xmltodict
import requests
from threading import Thread
import threading
import time
import math
import sys
import itertools
import random
from spice_api import spice
import sys
sys.path.append("Backend.")

from GenreDatabase import *
from helpers import *
from AnimeScraper import *

from multiprocessing.dummy import Pool

## Main Method Information

# CreateFile
#	Creates a Text file based off of a given MAL account name containing their most liked genres and genre groupings

## Kwargs List:

# smallest_group_size
#	Default Value: 2
# 	Description: Defines the smallest grouping of anime groups that it will recommend. Ex If smallest_group_size == 3, then "Horror/Thriller" will not be recommended, but "Horror/Thriller/Sci-Fi" might

# largest_group_size
#	Default Value: 4
# 	Description: Defines the largest grouping of anime groups that it will recommend. Ex If largest_group_size == 4, then "Horror/Thriller/Sci-Fi/Action/Adventure" will not be recommended, but "Horror/Thriller/Sci-Fi/Action" might

# new_groups
#	Default Value: False
# 	Description: Will only recommend genre groups that you have not watched yet

# current_groups
#	Default Value: False
# 	Description: Will only recommend genre groups that you have already watched

# sample_pool
#	Default Value: 'ALL' {Takes in int or 'ALL'}
# 	Description: The amount of genre groups to be returned from the genre group recommender

# recommend_types
#	Default Value: ['TV', 'Movie', 'Ova', 'Special', 'ONA']
# 	Description: What types of animes should be returned

# exclude_genres
#	Default Value: []
# 	Description: Takes in a list of genres you want excluded to be recommended

# include_genres
#	Default Value: []
# 	Description: Takes in a list of genres you want to be included in your recommendations {All animes given have to be in the recommended genres}

# nice_print
#	Default Value: False
# 	Description: Returns a nice text representation of the recommendations for easy printing

# cutoff
#	Default Value: 0.08
# 	Description: Genres that make up this % of animes you have watched will be displayed in your file

# types
#	Default Value: ["TV", "Movie", "Ova", "Special", "ONA"]
# 	Description: The types of animes that will be pulled from your MAL account

# status
#	Default Value: ['DROPPED', 'COMPLETED', 'PLAN TO WATCH', 'WATCHING', 'ON-HOLD']
# 	Description: The statuses of animes that will be pulled from your MAL account

# quiet
#	Default Value: False
# 	Description: Tells the program to print nothing {Viable for WillILike only!}

# text_output : WIL
#	Default Value: False
#	Description: Returns text instead of data{Viable for WillILike only!}


# NAME
#	Default Value:
# 	Description:


creds = spice.init_auth("Nikolai_Narma", "Coconutbananawertfuzzy77!")
class Analyzer:
	def __init__(self, ** kwargs):
		self.FileName = kwargs.get('name')

		f = spice.get_list(spice.get_medium('anime'), user = self.FileName, credentials = creds).raw_data
		parsed = xmltodict.parse(str(f))
		JSON = json.loads(json.dumps(parsed))['html']['body']['myanimelist']

		with open("Backend/Genres.json", 'r') as f:
			self.ID_TO_GENRES = json.load(f)

		self.ANIMES = JSON['anime']
		#print(self.ANIMES)
		self.INFO = JSON['myinfo']

		
		self.RETRIES = kwargs.get('retries', 10)
		self.CUTOFF_PERCENT = kwargs.get("cutoff", 0.08)
		self.TYPES = [x.upper() for x in kwargs.get('types', ["TV", "Movie", "Ova", "Special", "ONA"])]
		self.STATUS =  [x.upper() for x in kwargs.get('status', ['DROPPED', 'COMPLETED', 'PLAN TO WATCH', 'WATCHING', 'ON-HOLD'])]
		self.GenresByRating = GenreDatabase(name = self.FileName, cutoff = self.CUTOFF_PERCENT, ID = self.INFO['user_id'])
		self.COUNT = 0
		self.RATINGSLIST = []

	def getGenres(self, anime):

		if int(anime['my_score']) == 0:
			if int(anime['my_status']) == 4:
				anime['my_score'] = '0'
			else:
				return self

		self.RATINGSLIST.append(int(anime['my_score']))

		# If we have discovered this anime before
		if anime['series_animedb_id'] in self.ID_TO_GENRES.keys():
			#print("Found again")
			self.ID_TO_GENRES[anime['series_animedb_id']]['Ratings'][self.INFO['user_id']] = int(anime['my_score'])
			Search = None

			try:
				if type(self.ID_TO_GENRES[anime['series_animedb_id']]['Ratings']['0']) != float:
					Search = spice.search(anime['series_title'].replace("+", "_"), spice.get_medium('anime'), credentials = creds)

					if type(Search) == list:
						for entry in Search:
							if entry.id == anime['series_animedb_id']:
								Search = entry
								break

					if type(Search) == list:
						print(anime['series_animedb_id'], anime['series_title'], [(x.id, x.title) for x in Search])

					# print(spice.search(anime['series_title'].replace("+", "_"), spice.get_medium('anime'), credentials = creds).__dict__)

					self.ID_TO_GENRES[anime['series_animedb_id']]['Ratings']['0'] = float(Search.score)

					# print(self.ID_TO_GENRES[anime['series_animedb_id']]['Ratings']['0'])

				if self.ID_TO_GENRES[anime['series_animedb_id']].get("Episodes") == None:
					if Search == None:
						Search = spice.search(anime['series_title'].replace("+", "_"), spice.get_medium('anime'), credentials = creds)
						
						if type(Search) == list:
							for entry in Search:
								if entry.id == anime['series_animedb_id']:
									Search = entry
									break

					self.ID_TO_GENRES[anime['series_animedb_id']]['Episodes'] = Search.episodes

				if self.ID_TO_GENRES[anime['series_animedb_id']].get("Aired") == None:
					if Search == None:
						Search = spice.search(anime['series_title'].replace("+", "_"), spice.get_medium('anime'), credentials = creds)
						
						if type(Search) == list:
							for entry in Search:
								if entry.id == anime['series_animedb_id']:
									Search = entry
									break

					self.ID_TO_GENRES[anime['series_animedb_id']]['Aired'] = Search.dates		
			except Exception as e:
				print(e, anime['series_title'])
				time.sleep(2)
				# print("Rerunning")
				# self.getGenres(anime)
			self.COUNT += 1
			return self	

		# Scrape the Anime
		self.ID_TO_GENRES[anime['series_animedb_id']] = scrape_anime(self.INFO['user_id'], anime)

		self.COUNT += 1
		return self

	def runThreads(self):
		queue = []
		for anime in self.ANIMES:
			thr = Thread(target = self.getGenres, args = [anime])
			queue.append(thr)
		while len(queue) > 0:
			while threading.activeCount() <= 5 and len(queue) > 0:
				queue.pop().start()

		while(threading.activeCount() > 2):
			print("Waiting for finish... ({} remaining)".format(threading.activeCount() - 2))
			# print([x._args for x in threading.enumerate()])
			time.sleep(3)

		self.ANIMES = {}

		self.updateDatabase()

		return self

	def aggregate(self):

		self.GenresByRating.load_from_anime_list(self.ID_TO_GENRES.items(), self.INFO['user_id'])

		with open("Backend/GENRE_DUMP.json", 'w') as f:
			json.dump(self.GenresByRating.dictionary, f, indent = 4)
		return self

	def writeAnalysisToFile(self):
		sorted_genres = sorted([x0 for x0, x1 in self.GenresByRating.dictionary.items() if len(x0.split('-')) == 1], key=lambda t: self.GenresByRating.get_score([t]) if self.GenresByRating.get_score([t]) != None else 0, reverse = True)
		output = "Username: {}\nID: {}\nAnimes Analyzed: {}\nCut-off: {}%\nTypes: {}\nStatus: {}\n\n".format(self.INFO['user_name'], self.INFO['user_id'], self.COUNT, round(self.CUTOFF_PERCENT * 100, 1), ", ".join(self.TYPES), ", ".join(self.STATUS))
		
		# print(sorted_genres[0][0], sorted_genres[0][1])
		def generateTextFor(genres, new_genre, depth = 0, previous_score = 0):
			if self.GenresByRating.get_display(genres) == False:
				return ""

			Generated_For = {}

			if depth != 0:
				Text = "{}|{} {} with score {}\n".format((" " * depth * 2), "++" if self.GenresByRating.get_score(genres) >= previous_score else "--", new_genre, self.GenresByRating.get_score(genres))
			else:
				Text = "Genre Breakdown for {} with average score of {}\n".format(new_genre, self.GenresByRating.get_score(genres))

			for genre_set in self.GenresByRating.get_parent_genres(genres):
				genre = list(set(genre_set) - set(genres))[0]
				if genre in GENRES:
					generated = generateTextFor(genres + [genre], genre, depth + 1, self.GenresByRating.get_score(genres))
					if generated != "":
						Generated_For[genre] = generated

			sorted_keys = sorted(Generated_For.keys(), key = lambda x: self.GenresByRating.get_score(genres + [x]), reverse = True)

			for key in sorted_keys:
				#if tree_segment[key]['score'] > tree_segment['score']:
				Text += Generated_For[key]

			return Text

		for genre in sorted_genres:
			generated = generateTextFor([genre], genre)
			if generated != '':
				output += generated + "\n"


		#with open("Output\{}.txt".format(self.FileName), 'w') as f:
			#f.write(output)
		return self

	def updateDatabase(self):
		with open("Backend/Genres.json", 'w') as f:
			json.dump(self.ID_TO_GENRES, f, indent = 4)
		return self

# Creates a Text File with all of the information 
def CreateFile(name, ** kwargs):
	kwargs['name'] = name
	A = Analyzer(** kwargs)
	A.runThreads().aggregate().writeAnalysisToFile().updateDatabase()
	print("Output file named: '{}.txt'".format(kwargs.get('name')))
	return A

# def find_loc(db, genres):
# 	return Tree.

# 	t = Tree
# 	for genre in sorted(genres):
# 		if genre in t.get('subgenres', []):
# 			#print("Subgenre")
# 			return t
# 		t = t.get(genre, {})
# 	return t

def WillILike(name, genres, **kwargs):
	A = kwargs.get("A", None)

	if A == None:
		# print("New Analyzer")
		A = Analyzer(name = name).runThreads().aggregate().updateDatabase()
		# print("Done Analyzer")

	Scores = A.GenresByRating.get_super_score(genres)

	if len(Scores) == 0:
		Scores = [0]

	Score = round(sum(Scores)/len(Scores), 4)#, round(count/len(pairs) * 100, 2)

	# If you want printing
	if not kwargs.get('quiet', False):
		to_print = ""
		if Score > 0:
			to_print += "You rate this genre group {}% higher than normal.\n\n".format(Score)
		elif Score == 0:
			to_print += "You rate this genre about average.\n\n"
		else:
			to_print += "You rate this genre group {}% lower than normal.\n\n".format(-Score)

		GoodAnimes = []
		for id, data in A.ID_TO_GENRES.items():
			if set(data['Genres']) >= set(genres):
				# print(data['Genres'])
				# print(id, str(A.INFO['user_id']), list(data['Ratings'].keys()))
				if str(A.INFO['user_id']) in data['Ratings'].keys():
					GoodAnimes.append((data['Title'], int(data['Ratings'][A.INFO['user_id']]), data['Ratings']['0']))

		to_print += "Your top Animes with this pairing\n"
		top5 = ["{} - {} (MAL score: {})".format(anime[0], anime[1], anime[2]) for anime in sorted(GoodAnimes, key = lambda x: x[1], reverse = True)[:5]]
		to_print += "\n".join(top5) + "\n"

		if len(GoodAnimes) > 5:
			to_print += "\nYour bottom Animes with this pairing\n"
			bot5 = ["{} - {} (MAL score: {})".format(anime[0], anime[1], anime[2]) for anime in sorted(GoodAnimes, key = lambda x: x[1])[:5]]
			to_print += "\n".join(bot5) + "\n"

		return to_print

	return Score

def recommendGenreGroups(name, num = 10, **kwargs):
	A = kwargs.get("A", None)
	if A == None:
		A = Analyzer(name = name).runThreads().aggregate().updateDatabase()
	kwargs['A'] = A
	groupings =  helpers.get_Combinations([key for key in A.GenresByRating.dictionary.keys() if len(key.split("-")) == 1], lowest = kwargs.get("smallest_group_size", 2), highest = kwargs.get("largest_group_size", 4))

	Entries = {}
	for genres in groupings:
		Entries["/".join(genres)] = A.GenresByRating.get_score(genres) if A.GenresByRating.get_score(genres) != None else 0 # WillILike(name, genres, quiet = True, count_missing = True, **kwargs)

	if num == "ALL":
		num = len(Entries)
	return sorted(Entries.items(), key = lambda x: x[1], reverse = True)[:num]

def recommendAnimes(name, num=10, **kwargs):

	kwargs = kwargs['kwargs']
	A = kwargs.get("A", None)
	stime_1 = time.time()
	if A == None:

		stime = time.time()
		A = Analyzer(name = name)
		print("Creating Analyzer, {}s".format(int(time.time() - stime)))

		stime = time.time()
		A.runThreads()
		print("Running Threads, {}s".format(int(time.time() - stime)))

		stime = time.time()
		A.aggregate()
		print("Aggregating, {}s".format(int(time.time() - stime)))

		stime = time.time()
		A.updateDatabase()
		print("Updating Database, {}s".format(int(time.time() - stime)))


	print("Overall Analyzer, {}s".format(int(time.time() - stime_1)))
	stime = time.time()
	FoundGenreGroups = recommendGenreGroups(name, kwargs.get("sample_pool", "ALL"), A = A, **kwargs)
	print("Finding Groups, {}s".format(int(time.time() - stime)))
	retList = []
	ALLOWEDTYPES = [x.upper() for x in kwargs.get('recommend_types', ["TV", "Movie", "Ova", "Special", "ONA"])]

	MAX_EPISODES = kwargs.get('max_episodes', 100000000)
	MIN_EPISODES = kwargs.get('min_episodes', -1)

	FINDING_MULTIPLIER = kwargs.get("finding_multiplier", 200 / num)

	print(FINDING_MULTIPLIER)

	LAZY = kwargs.get("lazy", False)

	stime = time.time()
	used = set()
	# try:
	for genreGroup in FoundGenreGroups:
		# print("{}% complete".format(int(100 * len(retList) / (FINDING_MULTIPLIER * num))))

		for entry in used:
			if set(entry) < set(genreGroup):
				continue

		if list(genreGroup)[1] == 0:
			break
		print(genreGroup)
		# Look through our database for animes
		FoundAnimes = FindInDataBase(genreGroup[0].split('/'), ID_TO_GENRES = A.ID_TO_GENRES)

		# for every anime that we find
		for anime in FoundAnimes:

			if anime[1].get('INACTIVE'):
				continue

			# If contains a genre from the Excluded list
			if len(set(anime[1]['Genres']) & set(kwargs.get("exclude_genres", []))) != 0:
				continue

			# If contains all the animes from included list
			if set(anime[1]['Genres']) & set(kwargs.get("include_genres", [])) != set(kwargs.get("include_genres", [])):
				continue

			# If not in the Allowed Types
			if anime[1]['Type'].upper() not in ALLOWEDTYPES:
				continue

			# If we have already added this to our list
			if anime[1]['Title'] in [x[0] for x in retList]:
				continue
			
			# If you have already watched this anime
			if A.INFO['user_id'] in anime[1]['Ratings'].keys():
				continue

			Search = None
			if anime[1].get('Aired') == None or type(anime[1].get('Aired')) == str:
				if LAZY:
					continue
				print("Collecting Aired Data, {}".format(int(anime[0])))
				try:
					Search = spice.search_id(int(anime[0]), spice.get_medium('anime'), creds)
					A.ID_TO_GENRES[anime[0]]['Aired'] = Search.dates
					anime[1]['Aired'] = Search.dates
				except Exception:
					# del A.ID_TO_GENRES[anime[0]]
					print("Error trying to collect Aired data, {}".format(int(anime[0])))
					A.ID_TO_GENRES[anime[0]]['INACTIVE'] = True
					anime[1]['INACTIVE'] = True
					continue
				print("{}% complete".format(int(100 * len(retList) / (FINDING_MULTIPLIER * num))))


			if not valid_date(anime[1]['Aired'], after = kwargs.get("after_year"), before = kwargs.get("before_year")):
				continue

			if anime[1].get('Episodes') == None:
				if LAZY:
					continue
				print("Collecting Episode Data, {}".format(int(anime[0])))
				try:
					if Search == None:
						Search = spice.search_id(int(anime[0]), spice.get_medium('anime'), creds)
					A.ID_TO_GENRES[anime[0]]['Episodes'] = int(Search.episodes)
					anime[1]['Episodes'] = int(Search.episodes)
				except Exception:
					# del A.ID_TO_GENRES[anime[0]]
					print("Error trying to collect Episode data, {}".format(int(anime[0])))
					A.ID_TO_GENRES[anime[0]]['INACTIVE'] = True
					anime[1]['INACTIVE'] = True
					continue
				print("{}% complete".format(int(100 * len(retList) / (FINDING_MULTIPLIER * num))))

			if "Episodes" in str(anime[1].get('Episodes', "")):
				clean = anime[1]['Episodes'].split('\n')[2].strip()
				if clean == "Unknown":
					continue
				ep = int(clean)
				anime[1]['Episodes'] = ep
				A.ID_TO_GENRES[anime[0]]['Episodes'] = ep

			if anime[1]['Episodes'] == "Unknown" or int(anime[1]['Episodes']) > MAX_EPISODES or int(anime[1]['Episodes']) < MIN_EPISODES:
				continue

			# print((anime[1]['Title'], anime[0]))
			# print(anime[1]['Aired'])

			# print(anime[1])
			# -100 to 100, % rating difference, Ex 16% = rated 16% higher than normal
			# print("buh")
			Likeness = WillILike(name, anime[1]['Genres'], quiet = True, A = A, **kwargs)
			# 0-10, Rating of the anime
			Rating_Multiplier = anime[1]['Ratings']['0']
			# 
			Score = (Likeness * Rating_Multiplier * 2 + (Rating_Multiplier * 100)) / 10

			# print((anime[1]['Title'], round(Score, 2)))
			# print(anime[1].get('Aired'))
			retList.append((anime[1]['Title'], round(Score, 2)))
			# print("got_one: {}".format(len(retList)))

		if len(retList) > FINDING_MULTIPLIER * num:
			break
	# except Exception as e:
	# 	print("we broke something")
	# 	print(e)
	# 	pass

	print("Populating List, {}s".format(int(time.time() - stime)))

	A.updateDatabase()

	sortedList = sorted(retList, key = lambda x: x[1], reverse = True)
	print(kwargs)
	if kwargs.get('nice_print', False):
		print("nice")
		return "\n".join(["{}".format(AnimeInfo(x[0], nice_print = True)) for x in sortedList[:num]])
	else:
		return sortedList[:num]

def valid_date(date, after, before):
	year1 = date[0].split("-")[0]
	year2 = date[1].split("-")[0]
	# print(year1, year2)
	if after == None and before == None:
		return True
	if (after != None and (int(year1) >= after or int(year2) >= after)) and before == None:
		return True
	if after == None and (before != None and (int(year1) <= before or int(year2) <= before)):
		return True
	if (after != None and (int(year1) >= after or int(year2) >= after)) and (before != None and (int(year1) <= before or int(year2) <= before)):
		return True
	return False

with open("Backend/Genres.json", 'r') as f:
	ID_TO_GENRES = json.load(f)

GENRES_TO_ID = {}
for entry in ID_TO_GENRES.items():
	for genre in entry[1]['Genres']:
		if genre in GENRES_TO_ID.keys():
			GENRES_TO_ID[genre].append(entry[0])
		else:
			GENRES_TO_ID[genre] = [entry[0]]


def FindInDataBase(genreGroup, **kwargs):
	ID_TO_GENRES = kwargs.get("ID_TO_GENRES")
	if ID_TO_GENRES == None:
		with open("Backend/Genres.json", 'r') as f:
			ID_TO_GENRES = json.load(f)
	toRet = []
	currentIDs = []
	for genre in genreGroup:
		if len(currentIDs) == 0:
			currentIDs = GENRES_TO_ID[genre]
		else:
			currentIDs = set(currentIDs) & set(GENRES_TO_ID[genre])
	for ID in currentIDs:
		toRet.append((ID, ID_TO_GENRES[ID]))
	return toRet

def AnimesLikeThis(genreGroup, num = 10):
	combos = [combo for x in range(max(int(len(genreGroup)/2), 1), len(genreGroup)+1, 1) for combo in itertools.combinations(genreGroup, x)]
	animeGroups = [FindInDataBase(combo) for combo in combos]
	NameToScore = {}
	for animeGroup in animeGroups:
		for anime in animeGroup:
			if anime[1]['Title'] not in NameToScore.keys(): 
				numIn = [genre in anime[1]['Genres'] for genre in genreGroup].count(True)
				extra = len(anime[1]['Genres']) - numIn
				Rating = sum(anime[1]['Ratings'].values()) / len(anime[1]['Ratings'].values())
				NameToScore[anime[1]['Title']] = round(numIn/len(genreGroup) * math.pow(1.1, min(0, int(Rating-7))) * math.pow(0.95, extra), 3)
	sortedToScore = sorted(NameToScore.items(), key = lambda x: x[1], reverse = True)
	return sortedToScore[:num]

def Refresh_Database():
	p = Pool(10)
	IDs = helpers.get_IDs()

	def Collect_Data(AnimeID):
		try:
			site = requests.get("https://myanimelist.net/anime/"+ str(AnimeID))
			while site.status_code != 200 and site.status_code != 404:
				time.sleep(3)
				site = requests.get("https://myanimelist.net/anime/"+ str(AnimeID))

			soup = BeautifulSoup(site.text, "html.parser")
			rawGenres = soup.find('span', text='Genres:')
			Genres = [x.text for x in rawGenres.parent.find_all(href = True)]

			rawScore = soup.find('span', text='Score:')
			Score = rawScore.parent.find(itemprop = 'ratingValue').text

			Title = soup.find(itemprop = 'name').text

			rawType = soup.find('span', text='Type:')
			Type = rawType.parent.find('a').text

			try:
				Aired = spice.search_id(int(AnimeID), spice.get_medium('anime'), creds).dates
			except:
				Aired = None

			rawEpisodes = soup.find('span', text='Episodes:')
			Episodes = rawEpisodes.parent.text

			try:
				Episodes = int(Episodes.split('\n')[2].strip())
			except:
				Episodes = Episodes.split('\n')[2].strip()

			print("Adding {}".format(Title))

			return ( AnimeID, {
				'Genres' : Genres,
				'Ratings' : {'0' : float(Score)},
				'Title' : Title,
				'Type' : Type,
				'Aired' : Aired,
				'Episodes' : Episodes
				}
			)
		except:
			return None

	results = p.starmap(Collect_Data, zip(IDs))
	p.close()
	p.join()

	with open("Backend/Genres.json", 'r') as f:
		ID_TO_GENRES = json.load(f)

	for result in results:
		if result == None:
			continue
		ID, Dict = result
		if ID in ID_TO_GENRES.keys():
			# Save MAL_Rating
			ID_TO_GENRES[ID]['Ratings']['0'] = Dict['Ratings']['0']

			Dict['Ratings'] = ID_TO_GENRES[ID]['Ratings']

			ID_TO_GENRES[ID] = Dict

	with open("Backend/Genres_NEW.json", 'w') as f:
		json.dump(ID_TO_GENRES, f, indent = 4)



def AddMeLotsOfAnime(threads = 5, iterations = 10, **kwargs):
	for x in range(threads):
		Thread(target = PopulateList, args = [iterations], kwargs = kwargs).start()


def PopulateList(numAnimes = 1,  **kwargs):
	with open("Backend/Genres.json", 'r') as f:
		ID_TO_GENRES = json.load(f)

	queue = []
	results = []
	for x in range(numAnimes):
		results.append(getSomeRandomAnime(ID_TO_GENRES))	

	print(results)
	with open("Backend/Genres.json", 'r') as f:
		ID_TO_GENRES = json.load(f)
	for result in results:
		if result == None:
			continue
		ID, Dict = result
		if ID in ID_TO_GENRES.keys():
			ID_TO_GENRES[ID]['Aired'] = Dict['Aired']
		else:
			ID_TO_GENRES[ID] = Dict

	with open("Backend/Genres.json", 'w') as f:
			json.dump(ID_TO_GENRES, f, indent = 4)


with open("Backend/BAD_IDs.json") as f:
	BadIDs = json.load(f)['BadIDs']

def getSomeRandomAnime(data, ** kwargs):
	AnimeID = int(random.random() * 36700)

	while str(AnimeID) in data.keys() and data[str(AnimeID)].get("Aired", "") == "" or str(AnimeID) in BadIDs:
		AnimeID = int(random.random() * 36700)
	site = requests.get("https://myanimelist.net/anime/"+ str(AnimeID))
	retries = 0
	while site.status_code != 200 and retries < kwargs.get('retries', 20):
		while str(AnimeID) in data.keys() and data[str(AnimeID)].get("Aired", "") == "" or str(AnimeID) in BadIDs:
			AnimeID = int(random.random() * 36700)
		site = requests.get("https://myanimelist.net/anime/"+ str(AnimeID))
		retries += 1
		if site.status_code == 429:
			time.sleep(5)
		if site.status_code == 404:
			BadIDs.append(str(AnimeID))

	if retries == kwargs.get('retries', 20):
		print("too many retries")
		return
	try:
		soup = BeautifulSoup(site.text, "html.parser")
		rawGenres = soup.find('span', text='Genres:')
		Genres = [x.text for x in rawGenres.parent.find_all(href = True)]

		rawScore = soup.find('span', text='Score:')
		Score = rawScore.parent.find(itemprop = 'ratingValue').text

		Title = soup.find(itemprop = 'name').text

		rawType = soup.find('span', text='Type:')
		Type = rawType.parent.find('a').text

		try:
			Aired = spice.search_id(int(anime[0]), spice.get_medium('anime'), creds).dates
		except:
			rawAired = soup.find('span', text='Aired:')
			Aired = rawAired.parent.text

		rawEpisodes = soup.find('span', text='Episodes:')
		Episodes = rawEpisodes.parent.text

		print("Adding {}".format(Title))

		return ( AnimeID, {
			'Genres' : Genres,
			'Ratings' : {'0' : float(Score)},
			'Title' : Title,
			'Type' : Type,
			'Aired' : Aired,
			'Episodes' : int(Episodes.split('\n')[2].strip())
			}
		)
	except Exception as e:
		getSomeRandomAnime(data, **kwargs)

def TopX(name, num, **kwargs):
	A = kwargs.get("A", Analyzer(name = name).runThreads().aggregate())
	return sorted(A.GenresByRating.items(), key = lambda x: x[1]['score'] if x[1]['single'] and x[1]['display'] else 0, reverse = True)[:num]

def AnimeCompare(name1, name2, ** kwargs):
	kwargs['name'] = name1
	FirstA = Analyzer(** kwargs).runThreads().aggregate()
	kwargs['name'] = name2
	SecondA = Analyzer(** kwargs).runThreads().aggregate()
	toPrint = ""
	sorted1 = sorted(FirstA.GenresByRating.items(), key=lambda t: t[1]['score'], reverse = True)
	sorted2 = sorted(SecondA.GenresByRating.items(), key=lambda t: t[1]['score'], reverse = True)
	OneLikes_TwoLikes = {}
	OneLikes_TwoDislikes = {}
	OneDislikes_TwoLikes = {}
	OneDislikes_TwoDisLikes = {}

	for Person1Data in sorted1:
		if Person1Data[0] in [x[0] for x in sorted2]:

			FirstScoreSingle = str(FirstA.GenresByRating[Person1Data[0]]['score'])
			SecondScoreSingle = str(SecondA.GenresByRating[Person1Data[0]]['score'])



			toPrint += "{:27s} {}'s Score: {:5s} {}'s Score: {}\n".format(Person1Data[0], name1, FirstScoreSingle, name2, SecondScoreSingle)
			toPrint += "-"*70+"\n"

			for LookForGroup in sorted1:
				if Person1Data[0] in LookForGroup[0].split("/") and not LookForGroup[1]['single'] and LookForGroup[1]['display'] and LookForGroup[0] in [x[0] for x in sorted2]:
					catagory = LookForGroup[0].split("/")
					try:
						catagory.remove(Person1Data[0])
					except:
						pass

					FirstScoreDouble = str(FirstA.GenresByRating[LookForGroup[0]]['score'])
					SecondScoreDouble = SecondA.GenresByRating[LookForGroup[0]]['score']
					toPrint += "- {:25s} {}'s Score: {:5s} {}'s Score: {}\n".format("/".join(catagory), name1, FirstScoreDouble, name2, SecondScoreDouble)
			toPrint += "\n"
	print("File Output at '{}&{}.txt'".format(name1, name2))
	with open("Output\{}&{}.txt".format(name1, name2), 'w') as f:
		f.write(toPrint)
	return FirstA, SecondA

def AnimeInfo(animeName, ** kwargs):
	with open("Backend/Genres.json", 'r') as f:
		ID_TO_GENRES = json.load(f)
	for ID, Dict in ID_TO_GENRES.items():
		if Dict['Title'] == animeName:
			if not kwargs.get("nice_print", False):
				return Dict
			else:
				# Aired = extractAired(Dict.get("Aired", "Not Available"))
				# if len(Aired) == 2:
				# 	if Aired[1] == None:
				# 		Aired = "{} to now".format(Aired[0])
				# 	else:
				# 		Aired = "{} to {}".format(Aired[0], Aired[1])
				return "Title: {}\nType: {}\nGenres: {}\nEpisodes: {}\nAired: {}\nMAL Link: {}\n".format(Dict['Title'], Dict['Type'], ", ".join(Dict['Genres']), Dict['Episodes'], " to ".join(Dict['Aired']), MALLINK.format(ID, Dict['Title'].replace(" ", "_")))

def extractAired(Aired):
	if Aired == "Not Available":
		return "UNKNOWN"
	else:
		split = Aired.split('\n')[2].split(' ')
		if len(split) > 5:
			try:
				if split[6] == "?":
					return ("{} {}".format(split[2], split[4]), None)
				else:
					return ("{} {}".format(split[2], split[4]), "{} {}".format(split[6], split[8]))
			except:
				print(split)
				return None
		else:
			return ("{} {}".format(split[2], split[4]))
