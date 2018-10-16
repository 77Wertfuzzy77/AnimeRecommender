import searcher
import AnimeScraper
import Users

import json
import itertools
from functools import lru_cache
import time
from collections import defaultdict
from multiprocessing.dummy import Pool

def MAL_native_recommendation(username = 'Nikolai_Narma', raw = False, skip_watched = True):
	refresh_animes = []
	USER = Users.find_user_object(username)
	if USER.recommendations != None:
		return USER.recommendations
	USER_DATA = USER.user_data
	RECOMMENDATIONS = defaultdict(list)
	IDs = Users.find_user_object(username).complete_IDs
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
		score_diff = round(user_score/anime['score']/USER.average_difference, 2)
		for rec in anime.get('user_recommendations', []) if anime.get('user_recommendations', []) != None else []:
			if rec['mal_id'] in IDs and skip_watched:
				continue

			RECOMMENDATIONS[rec['mal_id']] += [score_diff] * int(rec['count']) + ([1] * (1+int(int(rec['count'])/4)))

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
	IDs = Users.find_user_object(username).complete_IDs
	# print(IDs)
	RECOMMENDATIONS = {}
	for rec in ANIMES:
		if rec['mal_id'] in IDs:
			continue
		RECOMMENDATIONS[rec['mal_id']] = [1]
	return RECOMMENDATIONS

def has_prequel(anime):
	return anime.get('related', {}).get('Prequel', []) not in [[], None]
check_1 = []
check_2 = []
check_3 = []
check_4 = []
check_5 = []
def score(anime, USER, avg_multiplier):
	t_time = time.time()

	genres = [x['name'] for x in anime['genre']]
	check_1.append(time.time() - t_time)

	staff_rating = USER.staff_rating(anime)
	check_2.append(time.time() - t_time)

	genre_rating = USER.genre_rating(genres)
	check_3.append(time.time() - t_time)

	studio_rating = USER.studio_rating(anime)
	check_4.append(time.time() - t_time)

	score = avg_multiplier * anime['score'] * genre_rating * studio_rating * staff_rating * USER.average_difference
	check_5.append(time.time() - t_time)
	return (score, genre_rating, studio_rating, staff_rating, avg_multiplier)

def enhanced_recommendations(username, kwargs):
	global check_1, check_2, check_3, check_4, check_5
	refresh_animes = []
	s_time = time.time()
	RECOMMENDATIONS = {**raw_recommendations(username, kwargs), **MAL_native_recommendation(username, raw = True)}
	# RECOMMENDATIONS = raw_recommendations(username, kwargs)
	print("Raw + Native MAL Recommendations took {}s".format(round(time.time() - s_time, 2)))

	s_time = time.time()
	USER = Users.find_user_object(username)
	print("Collecting User info took {}s".format(round(time.time() - s_time, 2)))

	def add_key(entry):

		mal_id, scores = entry
		anime = searcher.find_by_id(mal_id)
		# print(anime)
		if anime == None:
			anime = add_new_anime(mal_id)
			if anime == None:
				print("INVALID ID: {}".format(mal_id))
				return (mal_id, (0,))
			refresh_animes.append(anime)


		if has_prequel(anime) and not USER.watch_prequel(anime):
			return (mal_id, (0,))


		if searcher.resolve_kwargs(anime, kwargs):

			genres = [x['name'] for x in anime['genre']]
			avg_multiplier = sum(scores) / len(scores)
			if avg_multiplier != 1:
				avg_multiplier *= (1/USER.average_difference)

			my_score = score(anime, USER, avg_multiplier)

			# print(avg_multiplier, anime['score'], USER.genre_rating(genres), USER.studio_rating(anime), ENHANCED_RECOMMENDATIONS[key][0])
			return (mal_id, my_score)

			# print(avg_multiplier, anime['score'], USER.genre_rating(genres), USER.studio_rating(anime), ENHANCED_RECOMMENDATIONS[key][0])

		return (mal_id, (0,))

	s_time = time.time()
	ENHANCED_RECOMMENDATIONS = [add_key(x) for x in RECOMMENDATIONS.items()]
	print("Enhanced Recommendations took {}s".format(round(time.time() - s_time, 2)))
	print("Check 1: {}".format(sum(check_1)/len(check_1)))
	print("Check 2: {}".format(sum(check_2)/len(check_2)))
	print("Check 3: {}".format(sum(check_3)/len(check_3)))
	print("Check 4: {}".format(sum(check_4)/len(check_4)))
	print("Check 5: {}, {}".format(sum(check_5)/len(check_5), sum(check_5)))
	check_1 = []
	check_2 = []
	check_3 = []
	check_4 = []
	check_5 = []
	# print("Total Score Time: {}s, Avg: {}s".format(round(sum(score_times), 2), round(sum(score_times) / len(score_times), 2)))
	if len(refresh_animes) != 0:
		searcher.refresh(refresh_animes)
	return sorted(ENHANCED_RECOMMENDATIONS, key = lambda x :x[1][0], reverse = True)

def add_new_anime(ID):
	if searcher.find_by_id(ID) != None:
		print("Already have {} in the system!".format(ID))
		return None
	anime = AnimeScraper.Scrape(ID)
	return anime
