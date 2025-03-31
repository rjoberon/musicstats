#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Accessing and analysing a music library
#
# Usage:
#
# Author: rja
#
# Changes:
# 2024-11-13 (rja)
# - initial version copied from analyse.py

import re
import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

re_norm_title = re.compile(r"[^a-z ]")


#
# basic music collection functions
#

def get_songs(basedir, directory, excludes):
    """Traverse a directory and collect song metadata."""
    excludes = get_excludes(excludes) if excludes else []
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
    """Normalize a song title."""
    return " ".join(re_norm_title.sub("", title.lower()).split())


def get_excludes(fname):
    """Load excludes from file."""
    excludes = set()
    with open(fname, "rt") as f:
        for line in f:
            excludes.add(line.strip())
    return excludes
