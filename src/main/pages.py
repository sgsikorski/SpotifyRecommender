from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import os
from . import main

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from datetime import datetime
import random as rand

# Authentication
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:5050",
        scope="user-modify-playback-state",
    )
)


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
        session["songIndex"] = 0
    if "albumIndex" not in session:
        session["albumIndex"] = 0
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

    random_float = rand.random()
    skewed_float = random_float ** (1 / 3)
    year = int(1960 + skewed_float * (datetime.now().year - 1960))

    useSong = request.form.get("useSong") == "True"
    if useSong:
        spotifyRecs = []
        offset = session["songIndex"]
        while len(spotifyRecs) == 0:
            loadAmount = 25
            print(f'genre:"{genre}" year:{year}')
            tracks = sp.search(
                q=f"genre%3A{genre}%20year%3A{year}",
                type="track",
                limit=loadAmount,
                offset=offset,
                market="US",
            )
            for track in tracks["tracks"]["items"]:
                if track["popularity"] <= popularity:
                    spotifyRecs.append(track)
            if len(spotifyRecs) == 0:
                offset += loadAmount
            if offset + loadAmount >= offsetLimit:
                offset = 0
                year = rand.randint(1960, datetime.now().year)

        pickedSong = spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)]
        songTitle = pickedSong["name"]
        artist = pickedSong["artists"][0]["name"]
        sp.add_to_queue(pickedSong["uri"])
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
        loadAmount = 50
        print(f'genre:"{genre}" year:{year}')
        albums = sp.search(
            q=f"genre%3A{genre}%20year%3A{year}",
            type="album",
            limit=loadAmount,
            offset=offset,
            market="US",
        )
        for album in albums["albums"]["items"]:
            albumVal = sp.album(album["id"])
            if (
                albumVal["popularity"] <= popularity
                and albumVal["album_type"] == "album"
            ):
                spotifyRecs.append(album)
        if len(spotifyRecs) == 0:
            offset += loadAmount
        if offset + loadAmount >= offsetLimit:
            offset = 0
            year = rand.randint(1960, datetime.now().year)

    pickedAlbum = spotifyRecs[rand.randint(0, len(spotifyRecs) - 1)]
    albumTitle = pickedAlbum["name"]
    artist = pickedAlbum["artists"][0]["name"]
    return render_template(
        "recommendation.html",
        title=albumTitle,
        artistName=artist,
        song=pickedAlbum,
        spotifyLink=pickedAlbum["external_urls"]["spotify"],
        imageLink=pickedAlbum["images"][1]["url"],
        imageWidth=pickedAlbum["images"][1]["width"],
        imageHeight=pickedAlbum["images"][1]["height"],
        useSong=useSong,
        genre=genre,
        popularity=popularity,
    )
