#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Visualize albums as a timeline.
#
# Usage: see timeline.py -h
#
# Author: rja
#
# Changes:
# 2024-11-15 (rja)
# - initial version
#
# Prerequisites:
# - each album folder contains a cover image
# - the id3 metadata contains the publication year of the album

import os
import argparse
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
import numpy as np
import pandas as pd

VERSION = "0.0.1"


def get_songs(directory):
    """Traverse a directory and collect song metadata."""
    for pname in os.scandir(directory):
        if pname.is_dir():
            yield from get_songs(pname.path)
        else:
            song = get_song(pname)
            if song:
                yield song

def get_song(direntry):
    """Extract metadata from an mp3 file."""
    fname, path, ext = direntry.path.rpartition('.')   # get file extension
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
    df = pd.DataFrame(list(get_songs(directory)))

    # clean path
    df["path"] = df["path"].apply(os.path.dirname).apply(lambda x:os.path.relpath(x, directory))

    # drop songs
    albums = df[["path", "albumartist", "album", "year"]].drop_duplicates()
    # drop albums with missing year
    albums = albums.replace("", np.nan).dropna().reset_index(drop=True)
    # drop infrequent album artists
    albums = albums.groupby("albumartist").filter(lambda x: len(x) >= minfreq)
    # parse year as date
    albums["year"] = pd.to_datetime(albums["year"], format="%Y")

    # create stats
    stats = albums.groupby("albumartist").agg({"year" : ["min", "max", "count"]})
    stats = stats.reset_index().sort_values([("year", "min")], ascending=False)
    stats.columns = [' '.join(col).strip().replace(" ", "_") for col in stats.columns.values]

    return albums, stats


def plot_data_plotly(directory, albums, stats, cover_zoom=1.1, cover_file="cover.jpg"):
    """Plot the data using plotly express."""
    fig = px.timeline(stats, x_start="year_min", x_end="year_max", y="albumartist",
                      height=1000, opacity=0.3) #  color="year_count",

    # add album covers
    for aa in stats["albumartist"]:
        for _, album in albums[albums["albumartist"] == aa].iterrows():
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


def plot_data_pyplot(directory, albums, stats, cover_file="cover.jpg", out_file="timeline.png"):
    """Plot the data using pyplot."""
    mmin = stats["year_min"]
    mmax = stats["year_max"]

    plt.rcParams["figure.figsize"] = [16,9]
    ax = plt.subplot(111)
    plt.grid(zorder=0)
    ax.barh(stats["albumartist"], width=mmax - mmin, left=mmin, zorder=3, height=0.2)

    for aa in stats["albumartist"]:
        for _, album in albums[albums["albumartist"] == aa].iterrows():
            fname = os.path.join(directory, album["path"], cover_file)
            if os.path.isfile(fname):
                img = OffsetImage(mpimg.imread(fname), zoom=.03)
                ax.add_artist(AnnotationBbox(img, (album["year"], aa), frameon=False))

    plt.savefig(out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize albums as timeline',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('directory', type=str, help='input directory')
    parser.add_argument('mode', type=str, choices=["web", "file"], nargs='?', const="web",
                        help='output mode', default="web")
    parser.add_argument('-m', '--minfreq', type=int, metavar="F",
                        help='minimal number of albums per album artist', default=3)
    parser.add_argument('-c', '--cover', type=str, metavar="FILE",
                        help='cover file name', default="cover.jpg")
    parser.add_argument('-o', '--out', type=str, metavar="FILE",
                        help='output file name', default="timeline.png")
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + VERSION)

    args = parser.parse_args()

    albums, stats = load_data(args.directory, args.minfreq)

    if args.mode == "web":
        import plotly.express as px
        from PIL import Image
        from dash import Dash, dcc

        fig = plot_data_plotly(args.directory, albums, stats, cover_file=args.cover)
        app = Dash()
        app.layout = [dcc.Graph(figure=fig)]
        app.run(debug=True)
    else:
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox

        plot_data_pyplot(args.directory, albums, stats, cover_file=args.cover, out_file=args.out)
