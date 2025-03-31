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
# 2025-03-31 (rja)
# - migrated to use musicstats
# 2022-12-17 (rja)
# - finding near-duplicate artist names
# 2018-06-10 (rja)
# - initial version

import re
import argparse
from Levenshtein import distance
import musicstats

VERSION = "0.0.2"

#
# analysis functions
#
def similar_artists(songs, simrange, minlen):
    """Artists that differ only by some characters."""
    for s1 in songs:
        a1 = s1["artist"]
        for s2 in songs:
            a2 = s2["artist"]
            if a1 < a2 and min(len(a1), len(a2)) > minlen:
                dist = distance(normalise(a1), normalise(a2))
                if dist in simrange:
#                if dist / min(len(a1), len(a2)) < 1/4:
                    print(a1, s1, sep='\t')
                    print(a2, s2, sep='\t')


def same_but_special(songs, minlen):
    """Artists names that are same except for some special characters."""
    for s1 in songs:
        a1 = s1["artist"]
        for s2 in songs:
            a2 = s2["artist"]
            if a1 < a2 and min(len(a1), len(a2)) > minlen:
                if a1 != a2 and normalise(a1) == normalise(a2):
                    print(a1, s1, sep='\t')
                    print(a2, s2, sep='\t')


def normalise(s):
    """normalise strings to enable duplicate detection"""
    return re.sub(r'[\W_]+', '', s).lower()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='analyse audio library', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str, help='input directory', default="/home/rja/media/audio/library")
    parser.add_argument('-a', "--artists", action="store_true", help='find similar artists')
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE", help='exclude directories')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + VERSION)

    args = parser.parse_args()

    # do work
    songs = list(musicstats.get_songs(args.dir, args.dir, args.exclude))
#    if args.artists:
        # FIXME: wiederholen nach Normalisierung
    similar_artists(songs, range(2, 3), 5)
        # same_but_special(songs, 3)
