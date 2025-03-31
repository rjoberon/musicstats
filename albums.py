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


def get_maps(songs):
    """Returns album→songs and song→albums maps."""
    al_to_so = {}
    so_to_al = {}
    for song in songs:
        sid = get_song_id(song)
        album = song["album"]
        # fixme: song["album"] is not unique → use part of path
        if sid not in so_to_al:
            so_to_al[sid] = set()
        so_to_al[sid].add(song["album"])
        if album not in al_to_so:
            al_to_so[album] = set()
        al_to_so[album].add(sid)
    return al_to_so, so_to_al


def value_albums(al_to_so, so_to_al):
    values = {}
    for album in al_to_so:
        count = 0
        for song in al_to_so[album]:
            if len(so_to_al[song]) > 1:
                count += 1
        values[album] = count / len(al_to_so[album])
    return values



def get_song_id(song):
    #return song["artist"] + " : " + song["title"]
    return musicstats.normalize_title(song["title"]) + " : " + musicstats.normalize_title(song["artist"])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='analyse audio library', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str, help='input directory')
    parser.add_argument('-a', "--albums", action="store_true", help='print albums')
    parser.add_argument('-e', '--exclude', type=str, metavar="FILE", help='exclude directories')
    parser.add_argument("--expendable", action="store_true", help='print expendable albums')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + VERSION)

    args = parser.parse_args()

    # do work
    songs = musicstats.get_songs(args.dir, args.dir, args.exclude)
    if args.albums:
        albums = get_albums(songs)

        for a in albums:
            print(a)
    elif args.expendable:
        # print albums ordered by their fraction of songs that can be
        # found on other albums
        al_to_so, so_to_al = get_maps(songs)
        values = value_albums(al_to_so, so_to_al)
        for album in sorted(values, key=lambda i:values[i], reverse=True):
            if values[album] > 0.4:
                print(f"{values[album]:2.2f}: {album}")
                for song in al_to_so[album]:
                    if len(so_to_al[song]) < 2:
                        print("  ", song)
