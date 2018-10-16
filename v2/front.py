import processor
import Users
import searcher

def pretty(anime, USER, entry):
	MAL_LINK = "https://myanimelist.net/anime/{}"
	fmt = 'Title: {}\nGenres: {}\nMAl Score: {} Predicted Score: {}\nGenre:         {}%\nStudio:        {}%\nStaff:         {}%\nSimilar Anime: {}%\nLink: {}\n\n'
	return fmt.format(anime['title'],  ", ".join([x['name'] for x in anime['genre']]), anime['score'], int(entry[0] * USER.average_difference), round(entry[1] * 100 - 100, 1), round(entry[2] * 100- 100, 1), round(entry[3] * 100- 100, 1), round(entry[4] * 100- 100, 1), MAL_LINK.format(anime['mal_id']))

def pretty_html(anime, USER, entry):
	data = {}
	MAL_LINK = "https://myanimelist.net/anime/{}"
	data['name'] = anime['title']
	data['mal_score'] = anime['score']
	data['Predicted_Score'] = max(int(entry[0] * USER.average_difference), 10)
	data['Genres'] = ", ".join([x['name'] for x in anime['genre']])
	data['Genre_Grade'] = round(entry[1] * 100 - 100, 1)
	data['Studio_Grade'] = round(entry[2] * 100 - 100, 1)
	data['Staff_Grade'] = round(entry[3] * 100 - 100, 1)
	data['Related_Grade'] = round(entry[4] * 100 - 100, 1)
	data['Link'] = "https://myanimelist.net/anime/{}".format(anime['mal_id'])
	fmt = """
                <tr>
                  <td>
                    <a href="{Link}" title = "MyAnimeList Link">
                      <div class="anime-name">
                        {name}
                      </div>
                    </a>
                  </td>
                  <td>{mal_score}</td>
                  <td>{Predicted_Score}</td>
                  <td>{Genres}</td>
                  <td>{Genre_Grade}</td>
                  <td>{Studio_Grade}</td>
                  <td>{Staff_Grade}</td>
                  <td>{Related_Grade}</td>
                </tr>
	""".format(**data)
	return fmt

def rec(username = "Wertfuzzy77", count = 10, **kwargs):
	USER = Users.find_user_object(username)
	print("---------------------------------------------------------------------------")
	recommendations = processor.enhanced_recommendations(username, kwargs)[:count]
	for entry in recommendations:
		anime = searcher.find_by_id(entry[0])
		print(pretty(anime, USER, entry[1]))
		print("---------------------------------------------------------------------------")
	USER.dump()

def rec_html(username = "Wertfuzzy77", count = 10, **kwargs):
	USER = Users.find_user_object(username)
	htmls = []
	recommendations = processor.enhanced_recommendations(username, kwargs)[:count]
	for entry in recommendations:
		anime = searcher.find_by_id(entry[0])
		htmls.append(pretty_html(anime, USER, entry[1]))
	USER.dump()
	return htmls

def anime_console(username = None, **kwargs):
	if username == None:
		username = input("Username> ")
	USER = Users.find_user_object(username)
	while 1:
		found = anime(username, **kwargs)
		if found == None:
			return
		print(found)

def anime(username = None, **kwargs):
	if username == None:
		username = input("Username> ")
	USER = Users.find_user_object(username)
	anime_name = input("Anime> ")
	if anime_name.lower() in ['quit', 'q', 'quit()']:
		return

	try:
		anime = searcher.find_by_id(int(anime_name))
	except:
		anime_name = searcher.search_by_name(anime_name)[0][0]
		anime = searcher.find_by_name(anime_name)

	# print(anime_name, anime)

	rec_scores = processor.MAL_native_recommendation(username, raw = True, skip_watched = False)[anime['mal_id']]
	if len(rec_scores) == 0:
		avg_score = 1
	else:
		avg_score = sum(rec_scores)/len(rec_scores)

	entry = processor.score(anime, USER, avg_score)
	return pretty(anime, USER, entry)

# anime_console("Wertfuzzy77")
# print(anime())
# rec("ayayaa", type = 'TV', less_eps = 31, after_date = '2007', exclude_genres = ['Sports', 'Music', 'Slice of Life'], score_above = 8)

# Name = ""
# Parems = {'type' : 'TV', 'exclude_genres' : ['Sports']}
#
# with open("web/index_template.html") as f:
# 	with open("web/index.html", 'w', encoding = 'utf8') as w:
# 		 template = f.read()
# 		 htmls = rec_html("Wertfuzzy77", **Parems)
# 		 html_good = "".join(htmls)
# 		 w.write(template.format(html_good))
