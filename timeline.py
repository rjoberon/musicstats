#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Visualize albums as a timeline.
#
# Usage:
#
# Author: rja
#
# Changes:
# 2024-11-15 (rja)
# - initial version

from PIL import Image
from dash import Dash, html, dcc
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
import pandas as pd
import numpy as np
import plotly.express as px
import os
import datetime
import re
import argparse


version = "0.0.1"

def get_songs(directory):
    """Traverse a directory and collect song metadata."""
    for f in os.scandir(directory):
        if f.is_dir():
            for song in get_songs(f.path):
                yield song
        else:
            song = get_song(f)
            if song:
                yield song

def get_song(direntry):
    """Extract metadata from an mp3 file."""
    fname, p, ext = direntry.path.rpartition('.')   # get file extension
    if ext in ['pdf', 'jpg', 'wav', 'docx', 'rtf']: # ignore some extensions
        return None
    if ext == "flac":                               # handle audio file formats
        mut = FLAC(direntry.path)
    elif ext == "m4a":
        mut = MP4(direntry.path)
    elif ext == 'ogg':
        mut = OggVorbis(direntry.path)
    else:                                           # MP3 is the fallback
        mut = EasyID3(direntry.path)
    return get_metadata(direntry, mut)


def get_metadata(direntry, mut):
    """Extract metadata for one song."""
    return {
        "path" : direntry.path,
        "title" : get_value(mut, "title"),
        "artist" : get_value(mut, "artist"),
        "album" : get_value(mut, "album"),
        "albumartist" : get_value(mut, "albumartist", None),
        "year" : get_value(mut, "date"),
    }


def get_value(mut, key, default=""):
    """Get a (possibly missing) value for a key."""
    if key in mut:
        return mut[key][0]
    return default


def load_data(directory, minfreq=3):
    """Load and pre-process data."""
    df = pd.DataFrame([s for s in get_songs(directory)])

    # clean path
    df["path"] = df["path"].apply(os.path.dirname).apply(lambda x:os.path.relpath(x, directory))

    # drop songs
    albums = df[["path", "albumartist", "album", "year"]].drop_duplicates().replace("", np.nan).dropna().reset_index(drop=True).groupby("albumartist").filter(lambda x: len(x) >= minfreq)
    albums["year"] = pd.to_datetime(albums["year"], format="%Y")

    # create stats
    stats = albums.groupby("albumartist").agg({"year" : ["min", "max", "count"]}).reset_index().sort_values([("year", "min")], ascending=False)
    stats.columns = [' '.join(col).strip().replace(" ", "_") for col in stats.columns.values]

    return albums, stats


def plot_data(directory, albums, stats, cover_zoom=1.1, cover_file="cover.jpg"):
    """Plot the data."""
    fig = px.timeline(stats, x_start="year_min", x_end="year_max", y="albumartist", height=1000, opacity=0.3) #  color="year_count",

    # add album covers
    for aa in stats["albumartist"]:
        for i, album in albums[albums["albumartist"] == aa].iterrows():
            fname = os.path.join(directory, album["path"], cover_file)
            if os.path.isfile(fname):
                fig.add_layout_image(
                    source=Image.open(fname),
                    xref="x",
                    yref="y",
                    x=album["year"],
                    y=aa,
                    sizex=365*24*3600*1000 * cover_zoom,
                    sizey=1 * cover_zoom,
                    xanchor="center",
                    yanchor="middle"
                )
            else:
                print("missing:", album["path"])

    # style of plot
    fig.update_layout(
        plot_bgcolor = 'white'
    )

    return fig

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize albums as timeline', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('directory', type=str, help='input directory')
    parser.add_argument('-m', '--minfreq', type=int, metavar="F", help='minimal number of albums per album artist', default=3)
    parser.add_argument('-c', '--cover', type=str, metavar="FILE", help='cover file name', default="cover.jpg")
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + version)

    args = parser.parse_args()

    albums, stats = load_data(args.directory, args.minfreq)
    fig = plot_data(args.directory, albums, stats, cover_zoom=1.1, cover_file=args.cover)

    app = Dash()
    app.layout = [
        # html.Div(children='My Albums'),
        dcc.Graph(figure=fig)
    ]
    app.run(debug=True)
