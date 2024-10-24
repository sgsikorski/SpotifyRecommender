from flask import Flask, jsonify, request, render_template
import os
from . import main

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Authentication
client_credentials_manager = SpotifyClientCredentials(
    client_id=os.getenv("CLIENT_ID"), client_secret=os.getenv("CLIENT_SECRET")
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/filter", methods=["POST"])
def filter_items():
    search_term = request.json.get("term", "").lower()
    if search_term == "":
        return jsonify([])
    results = sp.search(q=search_term, type="track", limit=20)
    results = results["tracks"]["items"]
    return jsonify(results)


@main.route("/submit", methods=["POST"])
def submit():
    selected_item = request.form["items"]
    track = sp.track(selected_item)
    print(track)
    print()
    return render_template(
        "index.html",
        pop=track["popularity"],
        name=track["name"],
        artist=track["artists"][0]["name"],
    )
