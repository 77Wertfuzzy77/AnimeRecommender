import flask
from flask import request, jsonify, render_template

import Users
import searcher
import processor
import time
from front import pretty_html

app = flask.Flask(__name__)
app.config["DEBUG"] = True

def json_output(anime, USER, entry):
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
	return data

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Anime Recommendation API</h1>'''

@app.route('/recommendations', methods=['GET'])
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
    s_time = time.time()
    kwargs = convert(kwargs)



    recs = processor.enhanced_recommendations(name, kwargs)[:10]
    print("Done")
    USER = Users.find_user_object(name)
    data = "".join([pretty_html(searcher.find_by_id(x[0]), USER, x[1]) for x in recs])
    USER.dump()
    time_stamp = round(time.time() - s_time, 1)



    return render_template('recommendation.html', name=name, parameters = kwargs, time=time_stamp, recommendation_anime=data)

@app.route('/api/anime/recommendations/raw', methods=['GET'])
def raw():
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
    kwargs = convert(kwargs)
    recs = processor.enhanced_recommendations(name, kwargs)[:10]
    USER = Users.find_user_object(name)
    USER.dump()
    return jsonify([json_output(searcher.find_by_id(x[0]), USER, x[1]) for x in recs])

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

        if key == "after_year" or key == "before_year" or key == 'max_episodes' or key == "min_episodes" or key == "finding_multiplier" or key == 'less_eps':
            d[key] = int(d[key])

        if key == 'score_above':
            d[key] = float(d[key])

    return d

app.run(threaded=True)
