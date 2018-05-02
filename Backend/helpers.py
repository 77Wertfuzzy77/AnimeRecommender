import json
import itertools
import requests
from bs4 import BeautifulSoup as soup
import time

from multiprocessing.dummy import Pool

# Genres
Action = "Action"
Adventure = "Adventure"
Cars = "Cars"
Comedy = "Comedy"
Dementia = "Dementia"
Demons = "Demons"
Drama = "Drama"
Ecchi = "Ecchi"
Fantasy = "Fantasy"
Game = "Game"
Harem = "Harem"
Hentai = "Hentai"
Historical = "Historical"
Horror = "Horror"
Josei = "Josei"
Kids = "Kids"
Magic = "Magic"
Martial_Arts = "Martial Arts"
Mecha = "Mecha"
Military = "Military"
Music = "Music"
Mystery = "Mystery"
Parody = "Parody"
Police = "Police"
Psychological = "Psychological"
Romance = "Romance"
Samurai = "Samurai"
School = "School"
Sci_Fi = "Sci-Fi"
Seinen = "Seinen"
Shoujo = "Shoujo"
Shoujo_Ai = "Shoujo Ai"
Shounen = "Shounen"
Shounen_Ai = "Shounen Ai"
Slice_of_Life = "Slice of Life"
Space = "Space"
Sports = "Sports"
Super_Power = "Super Power"
Supernatural = "Supernatural"
Thriller = "Thriller"
Vampire = "Vampire"
Yaoi = "Yaoi"
Yuri = "Yuri"

MALLINK = "https://myanimelist.net/anime/{}/{}"

GENRES = [Action, Adventure, Cars, Comedy, Dementia, Demons, Drama, Ecchi, Fantasy, Game, Harem, Hentai, Historical, Horror, Josei, Kids, Magic, Martial_Arts, Mecha, Music, Mystery, Parody, Police, Psychological, Romance, Samurai, School, Sci_Fi, Seinen, Shoujo, Shoujo_Ai, Shounen, Shounen_Ai, Slice_of_Life, Space, Sports, Super_Power, Supernatural, Thriller, Vampire, Yaoi, Yuri]

TOP_URL = 'https://myanimelist.net/topanime.php?limit={}&type=tv'

def get_MAL_score(anime_id):
	with open("Backend/Genres.json", 'r') as f:
		return json.load(f)[anime_id]['Ratings']['0']

def get_MAL_scores(anime_ids):
	Scores = {}
	with open("Backend/Genres.json", 'r') as f:
		JSON = json.load(f)
		for ID in anime_ids:
			Scores[ID] = JSON[ID]['Ratings']['0']

	return Scores

def s(genres):
	return "-".join(sorted(genres))

def get_Combinations(genres, lowest = None, highest = None):
	if lowest == None:
		lowest = 0
	if highest == None:
		highest = len(genres)
	return [combo for x in range(lowest, highest+1) for combo in itertools.combinations(genres, x)]


def get_IDs(top = 1500):

	p = Pool(10)
	
	def scrape(url):
		print("Starting {}".format(url))
		site = requests.get(url)
		while site.status_code != 200:
			time.sleep(3)
			site = requests.get(url)
		x = soup(site.content, 'lxml')
		return [thing['href'].split('/')[4] for thing in x.find_all('a', href = True, text = True) if "https://myanimelist.net/anime/" in thing['href'] and '=' not in thing['href'] ]

	a = p.starmap(scrape, zip([TOP_URL.format(num) for num in range(top, -1, -50)]))
	p.close()
	p.join()

	return list(set([id for ids in a for id in ids]))