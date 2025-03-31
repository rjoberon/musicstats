#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Print statistics about my audio library
#
# Usage:
#
# Author: rja
#
# Changes:
# 2024-11-13 (rja)
# - initial version copied from analyse.py

import re
import argparse
import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from Levenshtein import distance

version = "0.0.1"

re_norm_title = re.compile(r"[^a-z ]")


#
# basic music collection functions
#

def get_songs(basedir, directory, excludes=[]):
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
    fname, path, ext = direntry.path.rpartition('.') # get file extension
    if ext in ['pdf', 'jpg', 'wav', 'docx', 'rtf']:  # ignore some extensions
        return None
    if ext == "flac":                                # handle audio file formats
        mut = FLAC(direntry.path)
    elif ext == "m4a":
        mut = MP4(direntry.path)
    elif ext == 'ogg':
        mut = OggVorbis(direntry.path)
    else:                                            # MP3 is the fallback
        mut = EasyID3(direntry.path)
    return get_metadata(direntry, mut)


def get_metadata(direntry, mut):
    """Extract metadata for one song."""
    return {
        "id" : direntry.path,
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


def normalize_title(title):
    return " ".join(re_norm_title.sub("", title.lower()).split())


def get_albums(songs):
    """Collect albums"""
    done = set()
    for song in songs:
        aa = song["albumartist"]
        if aa is not None:
            album = (aa, song["album"], song["year"])
            if album not in done:
                done.add(album)
                yield album


def get_excludes(fname):
    excludes = set()
    with open(fname, "rt") as f:
        for line in f:
            excludes.add(line.strip())
    return excludes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='analyse audio library', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str, help='input directory')
    parser.add_argument('-a', "--albums", action="store_true", help='print albums')
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE", help='exclude directories')
    parser.add_argument('-s', "--songs", action="store_true", help='print songs')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + version)

    args = parser.parse_args()

    excludes = get_excludes(args.exclude) if args.exclude else []

    # do work
    songs = get_songs(args.dir, args.dir, excludes)
    if args.albums:
        albums = get_albums(songs)

        for a in albums:
            print(a)
