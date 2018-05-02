import json
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from multiprocessing.dummy import Pool
import json

MAX_RETRIES = 5

def scrape_anime(userID, anime):
	# Try to get Site information
	site = requests.get("https://myanimelist.net/anime/"+ str(anime['series_animedb_id']))

	retries = 0
	while site.status_code != 200 and retries <= MAX_RETRIES:
		time.sleep(5)
		site = requests.get("https://myanimelist.net/anime/"+ str(anime['series_animedb_id']))
		retries += 1

	# If we retried too much
	if retries == MAX_RETRIES + 1:
		return self

	# Us Beautiful Soup to pull the Genres from the page
	soup = BeautifulSoup(site.text, "html.parser")
	rawGenres = soup.find('span', text='Genres:')
	Genres = [x.text for x in rawGenres.parent.find_all(href = True)]

	rawScore = soup.find('span', text='Score:')
	Score = rawScore.parent.find(itemprop = 'ratingValue').text

	try:
		Aired = spice.search_id(int(anime[0]), spice.get_medium('anime'), creds).dates
	except:
		rawAired = soup.find('span', text='Aired:')
		Aired = None

	rawEpisodes = soup.find('span', text='Episodes:')
	Episodes = rawEpisodes.parent.text
	if "Unknown" in Episodes:
		Episodes = "Episodes\n\n0"


	Scrapped = {
	'Genres' : Genres,
	'Ratings' : {userID : int(anime['my_score']), '0' : float(Score)},
	'Title' : anime['series_title'],
	'Type' : anime['series_type'] ,
	'Aired' : Aired ,
	'Episodes' : int(Episodes.split('\n')[2].strip())
	}
	print("Found a new Anime! ({})".format(anime['series_title']))

	return Scrapped


def Scrape(ID):
	link = "https://myanimelist.net/anime/{}".format(ID)
	site = requests.get(link)

	print(link)


	if site.status_code != 200:
		time.sleep(5)
		if site.status_code != 404:
			print("Retrying {} ({})".format(ID, site.status_code))
			return Scrape(ID)
		print("404 ERROR RESPONSE")
		return None

	soup = BeautifulSoup(site.text, "html.parser")

	try:
		mal_id = ID

		link_canonical = soup.find("link", rel = "canonical")['href']
		
		title = soup.find('title').text.replace("- MyAnimeList.net", "").strip()

		title_english = soup.find("span", text="English:")
		if title_english == None:
			pass
		else:
			title_english = ":".join(title_english.parent.text.split(":")[1:]).strip()

		title_japanese = soup.find("span", text="Japanese:")
		if title_japanese == None:
			pass
		else:
			title_japanese = ":".join(title_japanese.parent.text.split(":")[1:]).strip()

		title_synonyms = soup.find("span", text="Synonyms:")
		if title_synonyms == None:
			pass
		else:
			raw_title_synonyms = ":".join(title_synonyms.parent.text.split(":")[1:]).strip()
			title_synonyms = raw_title_synonyms.split(",")

		image_url = soup.find('img', itemprop = 'image', class_ = 'ac')['src']
		
		try:
			_type = soup.find('span', text = "Type:").next_sibling.next_sibling.text
		except:
			_type = soup.find('span', text = "Type:").next_sibling.strip()

		# print(_type)

		source = soup.find('span', text = "Source:").parent.text.split(":")[1].strip()

		episodes = soup.find('span', text = "Episodes:").parent.text.split(":")[1].strip()
		try:
			episodes = int(episodes)
		except:
			episodes = 0

		status = soup.find('span', text = "Status:").parent.text.split(":")[1].strip()

		airing = None

		aired_string = soup.find('span', text = "Aired:").parent.text.split(":")[1].strip()
		try:
			_from, _to = aired_string.split("to")
			_from_date = datetime.strptime(_from.strip(), '%b %d, %Y')
			_to_date = datetime.strptime(_to.strip(), '%b %d, %Y')
			_from = str(_from_date)
			_to = str(_to_date)

			aired = {
				"from" : _from,
				"to" : _to
			}

		except:
			# print(aired_string)
			try:
				aired_date = datetime.strptime(aired_string.strip(), '%b %d, %Y')
			except:
				aired_date = datetime.strptime(aired_string.strip(), '%b, %Y')
			aired = {
				"on" : str(aired_date)
			}
			#print("ERROR PARSING AIRED DATE")
			#return None


		duration = soup.find('span', text = "Duration:").parent.text.split(":")[1].strip()

		rating = soup.find('span', text = "Rating:").parent.text.split(":")[1].strip()

		score = float(soup.find('span', text = "Score:").next_sibling.next_sibling.text)

		scored_by = int(soup.find('span', itemprop = "ratingCount").text.replace(",", ""))

		try:
			rank = int(soup.find('span', text = "Ranked:").next_sibling.replace("#", "").strip())
		except:
			rank = None

		popularity = int(soup.find('span', text = "Popularity:").next_sibling.replace("#", "").strip())

		members = int(soup.find('span', text = "Members:").next_sibling.replace(",", "").strip())

		favorites = int(soup.find('span', text = "Favorites:").next_sibling.replace(",", "").strip())

		synopsis = soup.find('span', itemprop = "description").text

		background = None

		if soup.find('span', text = "Premiered:") != None:
			premiered = soup.find('span', text = "Premiered:").next_sibling.next_sibling.text
		else:
			premiered = None

		if soup.find('span', text = "Broadcast:") != None:
			broadcast = soup.find('span', text = "Broadcast:").parent.text.split(":")[1].strip()
		else:
			broadcast = None

		Adaptation = soup.find('td', text = "Adaptation:")
		if Adaptation != None:
			raw_Adaptation = Adaptation.next_sibling.find_all("a")
			Adaptation = []
			for adapt in raw_Adaptation:
				Adaptation.append({
					"type" : adapt['href'].split("/")[1],
					"mal_id" : adapt['href'].split("/")[2],
					"name" : adapt.text
					})

		Alternative_setting = soup.find('td', text = "Alternative setting:")
		if Alternative_setting != None:
			raw_Alternative_setting = Alternative_setting.next_sibling.find_all("a")
			Alternative_setting = []
			for adapt in raw_Alternative_setting:
				Alternative_setting.append({
					"type" : adapt['href'].split("/")[1],
					"mal_id" : adapt['href'].split("/")[2],
					"name" : adapt.text
					})

		Sequel = soup.find('td', text = "Sequel:")
		if Sequel != None:
			raw_Sequel = Sequel.next_sibling.find_all("a")
			Sequel = []
			for adapt in raw_Sequel:
				Sequel.append({
					"type" : adapt['href'].split("/")[1],
					"mal_id" : adapt['href'].split("/")[2],
					"name" : adapt.text
					})

		Other = soup.find('td', text = "Other:")
		if Other != None:
			raw_Other = Other.next_sibling.find_all("a")
			Other = []
			for adapt in raw_Other:
				Other.append({
					"type" : adapt['href'].split("/")[1],
					"mal_id" : adapt['href'].split("/")[2],
					"name" : adapt.text
					})

		Prequel = soup.find('td', text = "Prequel:")
		if Prequel != None:
			raw_Prequel = Prequel.next_sibling.find_all("a")
			Prequel = []
			for adapt in raw_Prequel:
				Prequel.append({
					"type" : adapt['href'].split("/")[1],
					"mal_id" : adapt['href'].split("/")[2],
					"name" : adapt.text
					})

		Alternative_version = soup.find('td', text = "Alternative version:")
		if Alternative_version != None:
			raw_Alternative_version = Alternative_version.next_sibling.find_all("a")
			Alternative_version = []
			for adapt in raw_Alternative_version:
				Alternative_version.append({
					"type" : adapt['href'].split("/")[1],
					"mal_id" : adapt['href'].split("/")[2],
					"name" : adapt.text
					})

		producer = [{"name":x.text, "link":x['href']} for x in soup.find('span', text = "Producers:").parent.find_all("a")]

		licensor = [{"name":x.text, "link":x['href']} for x in soup.find('span', text = "Licensors:").parent.find_all("a")]

		studio = [{"name":x.text, "link":x['href']} for x in soup.find('span', text = "Studios:").parent.find_all("a")]

		genre = [{"name":x.text, "link":x['href']} for x in soup.find('span', text = "Genres:").parent.find_all("a")]

		opening_theme = [x.text for x in soup.find("div", class_ = "theme-songs js-theme-songs opnening").find_all('span')]

		ending_theme = [x.text for x in soup.find("div", class_ = "theme-songs js-theme-songs ending").find_all('span')]

		# New Stuff

		try:
			characters = [{"name":x.text.strip(), "type":x.next_sibling.next_sibling.small.text.strip(), "voice" : x.parent.next_sibling.next_sibling.a.text.strip()} for x in soup.find("div", class_ = "detail-characters-list clearfix").find_all("a", href = True, class_ = False) if x.text.strip() != '' and "people" not in x['href']]
		except:
			characters = None

		try:
			staff = [{"name":x.text.strip(), "type":[y.strip() for y in x.next_sibling.next_sibling.small.text.strip().split(",")]} for x in soup.find_all("div", class_ = "detail-characters-list clearfix")[1].find_all("a", href = True, class_ = False) if x.text.strip() != '']
		except:
			staff = None

		try:
			user_recommendations = [{'title' : x['title'], "mal_id" : int(x.a['href'].split('-')[1]) if int(x.a['href'].split('-')[1]) != mal_id else int(x.a['href'].split('/')[-1].split('-')[0]), 'count' : x.a.find('span', class_ = 'users').text.split()[0]} for x in soup.find('ul', class_ = 'anime-slide js-anime-slide').find_all('li', class_ = 'btn-anime')]
		except:
			user_recommendations = None
		score_distribution = {
		10 : None,
		9 : None,
		8 : None,
		7 : None,
		6 : None,
		5 : None,
		4 : None,
		3 : None,
		2 : None,
		1 : None
		}
		score_distribution = None

		time_stamp = str(datetime.now())


		return {  
		   "mal_id":mal_id,
		   "link_canonical":link_canonical,
		   "title":title,
		   "title_english":title_english,
		   "title_japanese":title_japanese,
		   "title_synonyms":title_synonyms,
		   "image_url":image_url,
		   "type":_type,
		   "source":source,
		   "episodes":episodes,
		   "status":status,
		   "airing":airing,
		   "aired_string":aired_string,
		   "aired":aired,
		   "duration":duration,
		   "rating":rating,
		   "score":score,
		   "scored_by":scored_by,
		   "score_distribution": score_distribution, # NEW
		   "rank":rank,
		   "popularity":popularity,
		   "members":members,
		   "favorites":favorites,
		   "synopsis":synopsis,
		   "background":background,
		   "premiered":premiered,
		   "broadcast":broadcast,
		   "related":{  
		      "Adaptation":Adaptation,
		      "Alternative setting":Alternative_setting,
		      "Sequel":Sequel,
		      "Prequel":Prequel,
		      "Other":Other,
		      "Alternative version":Alternative_version
		   },
		   "producer":producer,
		   "licensor":licensor,
		   "studio":studio,
		   "genre":genre,
		   "opening_theme":opening_theme,
		   "ending_theme":ending_theme,

		   "characters":characters, # NEW
		   "staff":staff, # NEW
		   "user_recommendations":user_recommendations, # NEW

		   "time_stamp" : time_stamp}
	except:
		return None


def Data_Pull(IDs):
	p = Pool(5)

	Scrapped = p.starmap(Scrape, zip(IDs))
	p.close()
	p.join()

	return Scrapped

def run():
	with open("Genres.json") as f:
		database = json.load(f)
	IDs = [int(x) for x in database.keys()]

	scrapped = Data_Pull(IDs)

	with open("DATABASE.json", 'w') as f:
		json.dump(scrapped, f, indent = 4)
