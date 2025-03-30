#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
#
#
# Usage:
#
# Author: rja
#
# Changes:
# 2025-03-30 (rja)
# - initial version

from urllib.request import urlopen
import os.path
import re
from html import unescape

# <div class="performer"><a href="poplist.php?p=922#list">The Smiths</a></div><div><a href="poplist.php?t=1775#list">The Queen Is Dead</a></div>
re_song = re.compile(r"<div class=\"performer\"><a href=\"poplist.*?>(.*?)</a></div><div><a href=\"poplist.*?>(.*)</a></div>")


def get_page(url, fname):
    if os.path.isfile(fname):
        with open(fname, "rt") as f:
            return f.read()

    with open(fname, "wt") as f:
        html = urlopen(url).read().decode('utf-8')
        f.write(html)
        return html


def parse_page(html):
    # <div class="performer"><a href="poplist.php?p=922#list">The Smiths</a></div><div><a href="poplist.php?t=1775#list">The Queen Is Dead</a></div>
    for r in re_song.finditer(html):
        artist = unescape(r.group(1).strip())
        album = unescape(r.group(2).strip())
        print(artist, album, sep=": ")



if __name__ == '__main__':
   url = "https://poplist.de/poplist.php?site=1&var1=%20AND%20(tab_list_type.ID%20=%20959)&var4=Rolling%20Stone%20(2023)%20Die%20500%20besten%20Alben%20aller%20Zeiten%20-%20Kritiker&var5=Best-of-Lists%20from%20German%20Music%20Magazines%20-%20%20The%20500%20Best%20Albums%20of%20All%20Time&var10=Rolling%20Stone%20(2023)%20Die%20500%20besten%20Alben%20aller%20Zeiten,#list"

   for i in range(1, 6):
       html = get_page(url.replace("site=1", "site=" + str(i)), "rs_de_2023_" + str(i) + ".html")
       parse_page(html)
