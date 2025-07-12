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
# 2025-03-31 (rja)
# - refactored to use musicstats
# 2024-11-15 (rja)
# - initial version
#
# Prerequisites:
# - each album folder contains a cover image
# - the id3 metadata contains the publication year of the album

import os
import datetime
import argparse
import numpy as np
import pandas as pd
import musicstats

VERSION = "0.0.2"


def load_data(directory, excludes_fname, minfreq=3):
    """Load and pre-process data."""
    excludes = musicstats.get_excludes(excludes_fname) if excludes_fname else []
    df = pd.DataFrame(list(musicstats.get_songs(directory, directory, excludes)))

    # clean path
    df["path"] = df["id"].apply(os.path.dirname).apply(lambda x: os.path.relpath(x, directory))

    # drop songs
    albums = df[["path", "albumartist", "album", "year"]].drop_duplicates()
    # drop albums with missing year
    albums = albums.replace("", np.nan).dropna().reset_index(drop=True)
    # drop infrequent album artists
    albums = albums.groupby("albumartist").filter(lambda x: len(x) >= minfreq)
    # parse year as date
    albums["year"] = pd.to_datetime(albums["year"], format="%Y")

    # create stats
    stats = albums.groupby("albumartist").agg({"year": ["min", "max", "count"]})
    stats = stats.reset_index().sort_values([("year", "min")], ascending=False)
    stats.columns = [' '.join(col).strip().replace(" ", "_") for col in stats.columns.values]

    return albums, stats


def plot_data_plotly(directory, albums, stats, cover_zoom=1.1, cover_file="cover.jpg"):
    """Plot the data using plotly express."""
    fig = px.timeline(stats, x_start="year_min", x_end="year_max", y="albumartist",
                      height=1000, opacity=0.3)  # color="year_count",

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
        plot_bgcolor='white'
    )

    return fig


def plot_data_pyplot(directory, albums, stats, cover_file="cover.jpg", out_file="timeline.png"):
    """Plot the data using pyplot."""
    mmin = stats["year_min"]
    mmax = stats["year_max"]

    plt.rcParams["figure.figsize"] = [16, 9]
    ax = plt.subplot(111)
    ax.grid(axis="x", zorder=0)
    ax.tick_params(axis="both", which="both", length=0)
    ax.get_yaxis().set_visible(False)
    for sp in ["top", "right", "bottom", "left"]:
        ax.spines[sp].set_visible(False)
    ax.barh(stats["albumartist"], width=mmax - mmin, left=mmin, zorder=3, height=0.2)

    for aa in stats["albumartist"]:
        plt.text(stats[stats["albumartist"] == aa]["year_min"] - datetime.timedelta(days=365), aa, aa, ha="right", va="center")
        for _, album in albums[albums["albumartist"] == aa].iterrows():
            fname = os.path.join(directory, album["path"], cover_file)
            if os.path.isfile(fname):
                img = OffsetImage(mpimg.imread(fname), zoom=.03)
                ax.add_artist(AnnotationBbox(img, (album["year"], aa), frameon=False))
            else:
                print("missing:", album["path"])
    plt.tight_layout()
    plt.savefig(out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize albums as timeline',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('directory', type=str, help='input directory')
    parser.add_argument('mode', type=str, choices=["web", "file"], nargs='?',
                        const="web", help='output mode', default="web")
    parser.add_argument('-m', '--minfreq', type=int, metavar="F",
                        help='minimal number of albums per album artist', default=3)
    parser.add_argument('-c', '--cover', type=str, metavar="FILE",
                        help='cover file name', default="cover.jpg")
    parser.add_argument('-o', '--out', type=str, metavar="FILE",
                        help='output file name', default="timeline.png")
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE", help='exclude directories')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + VERSION)

    args = parser.parse_args()

    albums, stats = load_data(args.directory, args.exclude, args.minfreq)

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
