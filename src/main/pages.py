from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import os
from . import main

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import random as rand

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
    selected_item = request.form.get("items")
    if selected_item is None:
        return render_template("index.html")
    track = sp.track(selected_item)
    return render_template(
        "index.html",
        pop=track["popularity"],
        name=track["name"],
        artist=track["artists"][0]["name"],
    )


offsetLimit = 999


@main.route("/recommend", methods=["GET"])
def recommend():
    global offsetLimit
    error = request.args.get("error")
    if os.getenv("FLASK_CONFIG") == "development":
        return render_template(
            "recommend.html", available_genres=["Pop", "Rock"], error=error
        )
    genres = sp.recommendation_genre_seeds()
    genres = [g.capitalize() for g in genres["genres"]]
    return render_template("recommend.html", available_genres=genres, error=error)


@main.route("/recommendSubmit", methods=["POST"])
def recommendSubmit():
    if "songIndex" not in session:
        session["songIndex"] = rand.randint(0, offsetLimit)
    if "albumIndex" not in session:
        session["albumIndex"] = rand.randint(0, offsetLimit)
    genre = request.form.get("genre").lower()

    try:
        popularity = request.form.get("popularity")
        popularity = int(popularity)
        if popularity < 0 or popularity > 100:
            error = "Popularity must be between 0 and 100."
            return redirect(url_for("recommend"), error=error)
    except (ValueError, TypeError):
        return redirect(url_for("recommend"), error="Popularity must be an integer.")

    if popularity is None:
        popularity = 100

    useSong = request.form.get("useSong")
    if useSong:
        spotifyRecs = []
        offset = session["songIndex"]
        while len(spotifyRecs) == 0:
            loadAmount = 25
            tracks = sp.search(
                q=f"genre:{genre}",
                type="track",
                limit=loadAmount,
                offset=offset,
                market="US",
            )
            for track in tracks["tracks"]["items"]:
                if track["popularity"] <= popularity:
                    spotifyRecs.append(track)
            offset += loadAmount

        session["songIndex"] = offset

        print(spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)])
        pickedSong = spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)]
        songTitle = pickedSong["name"]
        artist = pickedSong["artists"][0]["name"]
        return render_template(
            "recommendation.html",
            title=songTitle,
            artistName=artist,
            spotifyLink=pickedSong["external_urls"]["spotify"],
            imageLink=pickedSong["album"]["images"][1]["url"],
            imageWidth=pickedSong["album"]["images"][1]["width"],
            imageHeight=pickedSong["album"]["images"][1]["height"],
            useSong=useSong,
            genre=genre,
            popularity=popularity,
        )

    spotifyRecs = []
    offset = session["albumIndex"]
    while len(spotifyRecs) == 0:
        loadAmount = 25
        albums = sp.search(
            q=f"genre:{genre}",
            type="album",
            limit=loadAmount,
            offset=offset,
            market="US",
        )
        for album in albums["albums"]["items"]:
            if sp.album(album["id"])["popularity"] <= popularity:
                spotifyRecs.append(album)
        offset += loadAmount
    session["albumIndex"] = offset

    print(spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)])
    pickedAlbum = spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)]
    songTitle = pickedAlbum["name"]
    artist = pickedAlbum["artists"][0]["name"]
    return render_template(
        "recommendation.html",
        title=songTitle,
        artistName=artist,
        song=spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)],
        spotifyLink=pickedAlbum["external_urls"]["spotify"],
        imageLink=pickedAlbum["images"][1]["url"],
        imageWidth=pickedAlbum["images"][1]["width"],
        imageHeight=pickedAlbum["images"][1]["height"],
        useSong=useSong,
        genre=genre,
        popularity=popularity,
    )
