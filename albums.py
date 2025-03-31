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

import argparse
import musicstats

VERSION = "0.0.1"


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='analyse audio library', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str, help='input directory')
    parser.add_argument('-a', "--albums", action="store_true", help='print albums')
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE", help='exclude directories')
    parser.add_argument('-s', "--songs", action="store_true", help='print songs')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + VERSION)

    args = parser.parse_args()

    # do work
    songs = musicstats.get_songs(args.dir, args.dir, args.excludes)
    if args.albums:
        albums = get_albums(songs)

        for a in albums:
            print(a)
