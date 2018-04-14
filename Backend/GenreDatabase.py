import json
import helpers
import math

from helpers import s

class GenreDatabase:
	def __init__(self, ** kwargs):
		self.name = kwargs.get("name")
		self.ID = kwargs.get("ID")
		self.average_difference = None
		self.Raw_Genre_Database = {}
		self.CUTOFF_PERCENT = kwargs.get("cutoff")
		self.COUNT = 0
		self.Super_Scores = {}

	def add(self, genres, rating, id, MAL_score):
		score = (((rating - self.average_difference) / MAL_score) - 1) * 100
		self.COUNT += 1
		for combo in helpers.get_Combinations(genres, lowest = 1):
			self.Raw_Genre_Database[s(combo)] = self.Raw_Genre_Database.get(s(combo), []) + [score]

	def get_score(self, genres):
		entry = self.Raw_Genre_Database.get(s(genres))
		if entry == None:
			return None
		else:
			if len(entry) < 3:
				entry += [0] * (3 - len(entry))
			return round(sum(entry) / len(entry), 2)
		# return self.Raw_Genre_Database.get(sorted(combo), {'Score'})

	def get_super_score(self, genres):
		# If we have a super score for this genre group
		if s(genres) in self.Super_Scores.keys():
			# print("found")
			return self.Super_Scores[s(genres)]

		# Get the score for this genre group
		raw_score = self.get_score(genres)
		if raw_score != None:
			Scores = [raw_score] * int(math.pow(2, len(genres)+1))
		else:
			Scores = []

		# For every child, add on their super scores
		for child in self.get_children_genres(genres):
			# print('child')
			Scores += self.get_super_score(child)

		# save the super score
		self.Super_Scores[s(genres)] = Scores

		return Scores

	def get_children_genres(self, Parent):
		Children = []
		for child in [key for key in self.Raw_Genre_Database.keys() if len(key.split('-')) == (len(Parent) - 1)]:
			child = child.split("-")
			if set(Parent) >= set(child):
				Children.append(child)
		return Children

	def get_parent_genres(self, Child):
		Parents = []
		for parent in [key for key in self.Raw_Genre_Database.keys() if len(key.split('-')) == (len(Child) + 1)]:
			parent = parent.split("-")
			if set(Child) <= set(parent):
				Parents.append(parent)
		return Parents

	def get_display(self, genres):
		entry = self.Raw_Genre_Database.get(s(genres))
		if entry == None:
			return False
		else:
			return len(entry) > self.COUNT * self.CUTOFF_PERCENT

	def set_average_differene(self, anime_list):
		self.average_difference = []
		# print(anime_list)
		for id, data in anime_list:
			self.average_difference.append(float(data['Ratings'][self.ID]) - data['MAL_score'])

		self.average_difference = sum(self.average_difference) / len(self.average_difference)	

	def load_from_anime_list(self, anime_list, userid):
		Processed_Data = {}
		for id, data in anime_list:
			if self.ID in data['Ratings'].keys():
				Processed_Data[id] = data

		MAL_scores = helpers.get_MAL_scores(Processed_Data.keys())

		for id, score in MAL_scores.items():
			Processed_Data[id]['MAL_score'] = score

		self.set_average_differene(Processed_Data.items())

		for id, data in Processed_Data.items():
			self.add(data['Genres'], int(data['Ratings'][self.ID]), id, data['MAL_score'])

	@property
	def dictionary(self):
		return self.Raw_Genre_Database


