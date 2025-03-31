#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Prints titles sorted by count.
#
# Usage:
#
# Author: rja
#
# Changes:
# 2025-03-31 (rja)
# - migrated to using albumstats
# - sorting titles by frequency
# 2018-06-10 (rja)
# - initial version

import re
import argparse
import os
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
import albumstats

version = "0.0.2"


#
# traverses a directory and collects title names
#
def get_titles(directory, excludes):
    titles = dict()
    songs = albumstats.get_songs(directory, directory, excludes)
    for song in songs:
        title = albumstats.normalize_title(song["title"])
        if title not in titles:
            titles[title] = []
        titles[title].append(song["id"])
    return titles

#
# prints title information
#
def print_titleinfo(title, paths, basedir, indent="   "):
    print(title)
    for path in paths:
        print(indent, path[len(basedir):])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='audio library statistics', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str, help='input directory', default="/home/rja/media/audio/library")
#    parser.add_argument('-a', "--add",  type=int, default="1", metavar="J", help='column in FILE1 which should be added to FILE2 (after column I)')
#    parser.add_argument('-s', "--skip", action="store_true", help='skip first line in FILE2')
#    parser.add_argument('-t', "--sep",  type=str, default="\t", metavar="SEP", help='column separator')
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE", help='exclude directories')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + version)

    args = parser.parse_args()

    excludes = albumstats.get_excludes(args.exclude) if args.exclude else []

    # do work
    titles = get_titles(args.dir, excludes)
    for title in sorted(titles, key=lambda i:len(titles[i]), reverse=True):
        paths = titles[title]
        if len(paths) > 1:
            print_titleinfo(title, paths, args.dir)

    print(len(titles), "titles processed")
