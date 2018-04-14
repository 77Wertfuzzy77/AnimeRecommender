import flask
from flask import request, jsonify

from Backend.GenreAnalyzer import *

app = flask.Flask(__name__)
app.config["DEBUG"] = True

# Create some test data for our catalog in the form of a list of dictionaries.

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Anime Recommendation API</h1>'''


@app.route('/api/v1/resources/anime', methods=['GET'])
def api_id():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'name' in request.args:
        name = request.args['name']
    else:
        return "Error: No name field provided. Please specify an name."

    A = Analyzer(name = name).runThreads().aggregate()

    # Use the jsonify function from Flask to convert our list of
    # Python dictionaries to the JSON format.
    return jsonify(A.GenresByRating.dictionary)

@app.route('/api/v1/resources/anime/recommendations', methods=['GET'])
def recommendations():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'name' in request.args:
        name = request.args['name']
    else:
        return "Error: No name field provided. Please specify an name."

    # print(kwargs)

    kwargs = {}
    for key in request.args:
        if key != 'name':
            kwargs[key] = request.args[key]

    return jsonify(recommendAnimes(name, kwargs = convert(kwargs)))

    # Use the jsonify function from Flask to convert our list of
    # Python dictionaries to the JSON format.
    # return jsonify(A.GenresByRating.dictionary)

@app.route('/api/v1/resources/anime/recommendations/pretty', methods=['GET'])
def recommendations_pretty():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'name' in request.args:
        name = request.args['name']
    else:
        return "Error: No name field provided. Please specify an name."

    # print(kwargs)

    kwargs = {}
    for key in request.args:
        if key != 'name':
            kwargs[key] = request.args[key]

    kwargs['nice_print'] = True

    return "<pre>" + recommendAnimes(name, kwargs = convert(kwargs)) + "</pre>"

    # Use the jsonify function from Flask to convert our list of
    # Python dictionaries to the JSON format.
    # return jsonify(A.GenresByRating.dictionary)

def convert(d):
    for key in list(d.keys()):
        if key == "types":
            ["TV", "Movie", "Ova", "Special", "ONA"]
            value = str(d[key])
            value = (5-len(value))*"0" + value 
            TV, Movie, Ova, Special, ONA = d[key]
            print(TV, Movie, Ova, Special, ONA)
            temp = []
            if TV != "0":
                temp.append("TV")
            if Movie != "0":
                temp.append("Movie")
            if Ova != "0":
                temp.append("Ova")
            if Special != "0":
                temp.append("Special")
            if ONA != "0":
                temp.append("ONA")

            d['recommend_types'] = temp

        if key == "include_genres":
            d[key] = d[key].split("|")

        if key == "exclude_genres":
            d[key] = d[key].split("|")

        if key == "after_year" or key == "before_year" or key == 'max_episodes' or key == "min_episodes":
            d[key] = int(d[key])

    return d

app.run()