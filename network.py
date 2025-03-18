#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Visualize songs and artists as a network.
#
# Usage: see network.py -h
#
# Author: rja
#
# Changes:
# 2025-03-18 (rja)
# - initial version
#

import os
import re
import argparse
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

VERSION = "0.0.1"

re_norm = re.compile(r"[^a-z ]")


def get_songs(basedir, directory, excludes):
    """Traverse a directory and collect song metadata."""
    for pname in os.scandir(directory):
        if pname.is_dir():
            if os.path.relpath(pname.path, basedir) not in excludes:
                yield from get_songs(basedir, pname.path, excludes)
            else:
                print("excluded", pname.path)
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


def load_data(directory, excludes=[]):
    """Load and pre-process data."""
    songs = dict()
    artists = dict()
    for song in get_songs(directory, directory, excludes):
        title_norm = normalize_title(song["title"])
        if len(title_norm) > 0:
            songs[title_norm] = song["title"]
            if title_norm not in artists:
                artists[title_norm] = set()
            artists[title_norm].add(normalize_artist(song["artist"]))

    return artists, songs


def filter_songs(artists, songs, minfreq=2):
    new_artists = dict()
    for song in artists:
        if len(artists[song]) >= minfreq:
            new_artists[song] = artists[song]
        else:
            del songs[song]
    return new_artists


def normalize_title(title):
    return " ".join(re_norm.sub("", title.lower()).split())


def normalize_artist(artist):
    return artist


def print_graph(artists, songs, outf):
    with open(outf, "wt") as f:
        print("graph G {", file=f)
        print("graph [outputorder=edgesfirst, overlap=false];", file=f)
        for song in songs:
            print('"s_' + song + '" [label="' + clean(songs[song]) + '",style=filled];', file=f)
        for song in artists:
            for artist in artists[song]:
                print('"s_' + song + '" -- "' + clean(artist) + '";', file=f)
        print("}", file=f)


def clean(s):
    return s.replace('"', '')


def get_excludes(fname):
    excludes = set()
    with open(fname, "rt") as f:
        for line in f:
            excludes.add(line.strip())
    return excludes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize songs and artists as network',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('directory', type=str, help='input directory')
    parser.add_argument('-o', '--out', type=str, metavar="FILE",
                        help='output file name', default="network.dot")
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE",
                        help='exclude directories')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + VERSION)

    args = parser.parse_args()

    if args.exclude:
        excludes = get_excludes(args.exclude)
    else:
        excludes = []

    artists, songs = load_data(args.directory, excludes)
    print("songs:", len(songs))
    artists = filter_songs(artists, songs)
    print("songs:", len(songs), "(after filtering)")
    print_graph(artists, songs, args.out)
