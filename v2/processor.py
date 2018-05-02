import searcher
import AnimeScraper
import Users

import json
import itertools
from functools import lru_cache
import time
from collections import defaultdict
from multiprocessing.dummy import Pool


def MAL_native_recommendation(username = 'Nikolai_Narma', raw = False):
	refresh_animes = []
	USER = Users.find_user_object(username)
	if USER.recommendations != None:
		return USER.recommendations
	USER_DATA = USER.user_data
	RECOMMENDATIONS = defaultdict(list)
	IDs = Users.find_user_object(username).IDs
	for user_anime in USER_DATA:
		if user_anime['status'] != 2:
			continue
		# print(user_anime)
		mal_id = user_anime['anime_id']
		user_score = user_anime['score']

		# Confirming we got the Anime
		anime = searcher.find_by_id(mal_id)
		if anime == None:
			anime = add_new_anime(mal_id)
			if anime == None:
				print("INVALID ID")
				continue
			# Queue this to add to database
			refresh_animes.append(anime)
		score_diff = round(user_score/anime['score'], 2)
		for rec in anime.get('user_recommendations', []) if anime.get('user_recommendations', []) != None else []:
			if rec['mal_id'] in IDs:
				continue

			RECOMMENDATIONS[rec['mal_id']] += [score_diff] * int(rec['count']) + ([1] * (1+int(int(rec['count'])/2)))

	# for key in list(RECOMMENDATIONS.keys()):
	# 	RECOMMENDATIONS[key] = sum(RECOMMENDATIONS[key]) / len(RECOMMENDATIONS[key]) * (1 + (len(RECOMMENDATIONS[key]) / 500))
	USER.recommendations = RECOMMENDATIONS
	if len(refresh_animes) != 0:
		searcher.refresh(refresh_animes)
	if raw:
		return RECOMMENDATIONS
	return sorted(RECOMMENDATIONS.items(), key = lambda x :sum(x[1]) / len(x[1]), reverse = True)

def raw_recommendations(username, kwargs):
	ANIMES = searcher.find_kwargs(**kwargs)
	USER_DATA = Users.find_user_object(username).user_data
	IDs = Users.find_user_object(username).IDs
	# print(IDs)
	RECOMMENDATIONS = {}
	for rec in ANIMES:
		if rec['mal_id'] in IDs:
			continue
		RECOMMENDATIONS[rec['mal_id']] = [1]
	return RECOMMENDATIONS

def has_prequel(anime):
	return anime.get('related', {}).get('Prequel', []) not in [[], None]

def enhanced_recommendations(username, kwargs):
	refresh_animes = []
	s_time = time.time()
	RECOMMENDATIONS = {**raw_recommendations(username, kwargs), **MAL_native_recommendation(username, raw = True)}
	# RECOMMENDATIONS = raw_recommendations(username, kwargs)
	print("Raw + Native MAL Recommendations took {}s".format(round(time.time() - s_time, 2)))

	ENHANCED_RECOMMENDATIONS = defaultdict(list)

	s_time = time.time()
	USER = Users.find_user_object(username)
	print("Collecting User info took {}s".format(round(time.time() - s_time, 2)))
	
	def add_key(key):
		mal_id = key
		anime = searcher.find_by_id(mal_id)
		# print(anime)
		if anime == None:
			anime = add_new_anime(mal_id)
			if anime == None:
				print("INVALID ID: {}".format(mal_id))
				return 
			refresh_animes.append(anime)

		if has_prequel(anime) and not USER.watch_prequel(anime):
			return

		genres = [x['name'] for x in anime['genre']]
		avg_multiplier = sum(RECOMMENDATIONS[key]) / len(RECOMMENDATIONS[key])
		if avg_multiplier != 1:
			avg_multiplier *= (1/USER.average_difference)
		if searcher.resolve_kwargs(anime, kwargs):
			# print(avg_multiplier, anime['score'], USER.genre_rating(genres), USER.studio_rating(anime), ENHANCED_RECOMMENDATIONS[key][0])
			staff_rating = USER.staff_rating(anime)
			genre_rating = USER.genre_rating(genres)
			studio_rating = USER.studio_rating(anime)
			score = avg_multiplier * anime['score'] * genre_rating * studio_rating * staff_rating
			ENHANCED_RECOMMENDATIONS[key] = (score, genre_rating, studio_rating, staff_rating, avg_multiplier)
			# print(avg_multiplier, anime['score'], USER.genre_rating(genres), USER.studio_rating(anime), ENHANCED_RECOMMENDATIONS[key][0])
	
	p = Pool(5)
	s_time = time.time()
	p.map(add_key, RECOMMENDATIONS.keys())
	print("Enhanced Recommendations took {}s".format(round(time.time() - s_time, 2)))
	if len(refresh_animes) != 0:
		searcher.refresh(refresh_animes)
	return sorted(ENHANCED_RECOMMENDATIONS.items(), key = lambda x :x[1][0], reverse = True)


def rec(username = "Nikolai_Narma", count = 10, **kwargs):
	USER = Users.find_user_object(username)
	print("---------------------------------------------------------------------------")
	fmt = 'Title: {}\nGenres: {}\nMAl Score: {} Predicted Score: {}\nGenre:         {}%\nStudio:        {}%\nStaff:         {}%\nSimilar Anime: {}%\nLink: {}\n\n'
	MAL_LINK = "https://myanimelist.net/anime/{}"
	recommendations = enhanced_recommendations(username, kwargs)[:count]
	for entry in recommendations:
		anime = searcher.find_by_id(entry[0])
		print(fmt.format(anime['title'],  ", ".join([x['name'] for x in anime['genre']]), anime['score'], int(entry[1][0] * USER.average_difference), round(entry[1][1] * 100 - 100, 1), round(entry[1][2] * 100- 100, 1),round(entry[1][3] * 100- 100, 1), round(entry[1][4] * 100- 100, 1), MAL_LINK.format(anime['mal_id'])))
	print("---------------------------------------------------------------------------")	
	USER.dump()




def add_new_anime(ID):
	if searcher.find_by_id(ID) != None:
		print("Already have {} in the system!".format(ID))
		return None
	anime = AnimeScraper.Scrape(ID)	
	return anime

