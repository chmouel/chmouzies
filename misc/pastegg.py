#!/usr/bin/env python3
"""
This will post the current text selection using xsel to paste.gg
This will guess very hard the content of the current selection with file and
custom magic type.
If that doesn't work it will ask for the content type via a rofi menu.

It will open a webbrowser at the end (or print it on stdout) the resulted
url.
"""
import datetime
import json
import mimetypes
import os
import pathlib
import subprocess
import sys
import tempfile
import webbrowser

import requests

EXPIRATION_HOURS = 24

RAW_PROGRAMMING_MAGIC = r"""
0       string             =<?php         PHP text
!:mime  text/x-php

0       string             =<?xml
>5      search/2048/c      =<svg          SVG text
!:mime  image/svg+xml

0       string             =def:        Python text
!:mime  text/x-python

0       string             =<?xml         XML text
!:mime  text/xml
0       regex/c            =^<phpunit  XML text without header
!:mime  text/xml

0       search/2048/c      =font-size:    Cascading Style Sheet text
!:mime  text/css
0       search/2048/c      =color:        Cascading Style Sheet text
!:mime  text/css
0       search/2048/c      =width:        Cascading Style Sheet text
!:mime  text/css

0       string             =---\          Difference file text
!:mime  text/diff
0       string             =diff          Difference file text
!:mime  text/diff

0       regex/c            =^[a-z]+=[a-z0-9]+  Windows INI configuration text
!:mime  text/ini

0       regex/c            =\s*\\$\\(     Javascript with jQuery text
!:mime  application/javascript

0       search/2048        =-------       reStructuredText text
!:mime  text/x-rst
0       search/2048        ========       reStructuredText text
!:mime  text/x-rst

0       search/2048/c      CREATE\ TABLE  SQL text
!:mime  text/x-sql
0       search/2048/c      DROP\ DATABSE  SQL text
!:mime  text/x-sql

0       search/2048        =\ PAGE\n      TypoScript text
!:mime  text/x-typoscript
0       search/2048        =\ USER\n      TypoScript text
!:mime  text/x-typoscript
0       search/2048        =\ TEXT\n      TypoScript text
!:mime  text/x-typoscript
0       search/2048        =.stdWrap      TypoScript text
!:mime  text/x-typoscript
0       search/2048        =stdWrap.      TypoScript text
!:mime  text/x-typoscript
"""

MAP_FILETYPE_STRING_TO_FILENAME = {
    "Python script": "text/x-python",
    "Bourne-Again": "text/x-shellscript"
}


def runcmd(cmd):
    ret = subprocess.run(cmd, shell=True, check=True, capture_output=True)
    if ret.returncode != 0:
        raise Exception(f"Cannot run {cmd}: {ret.stdout}")
    return ret.stdout.decode()


def detect_filetype(text):
    """Try a lot of different ways to guess mimetypes, faillign back to a rofi
    menu"""
    contentfile = tempfile.NamedTemporaryFile(delete=False).name
    magicfile = tempfile.NamedTemporaryFile(delete=False).name
    open(contentfile, 'w').write(text)
    open(magicfile, 'w').write(RAW_PROGRAMMING_MAGIC)
    ret = runcmd(f"file -m/usr/share/file/magic:{magicfile} -b {contentfile}")
    for ft in MAP_FILETYPE_STRING_TO_FILENAME:
        if ft in ret:
            os.remove(magicfile)
            os.remove(contentfile)
            return MAP_FILETYPE_STRING_TO_FILENAME[ft]
    ret = runcmd(f"file -ib {contentfile}")
    ret = ret.split(";")[0]
    if ret == "text/plain":
        ret = runcmd(
            "sed -n '/python-code/d;/^#/d;/^$/d;s/[ \t].*$//;p' /etc/mime.types |rofi -dmenu -select text/plain"
        )
    os.remove(magicfile)
    os.remove(contentfile)
    return ret


def pasteit(text=None):
    if not text:
        text = runcmd("xsel")
    filetype = detect_filetype(text).strip()
    extension = mimetypes.guess_extension(filetype) or ".txt"

    r = requests.post("https://api.paste.gg/v1/pastes",
                      headers={"Content-Type": "application/json"},
                      json={
                          "name":
                          f'Paste from {os.environ["USER"]}',
                          "visibility":
                          "unlisted",
                          "expires":
                          (datetime.datetime.now() +
                           datetime.timedelta(hours=EXPIRATION_HOURS)
                           ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "files": [{
                              "name": f"paste{extension}",
                              "content": {
                                  "format": "text",
                                  "value": text.encode()
                              }
                          }]
                      })
    r.raise_for_status()
    output = r.json()
    if output['status'] != 'success':
        return ""
    url = "https://paste.gg/p/anonymous/" + output['result']['id']
    if extension == '.txt':
        url += f"/files/{output['result']['files'][0]['id']}/raw"

    resultpath = pathlib.Path("~/.cache/pastegg/results.json").expanduser()
    if not resultpath.parent.exists():
        resultpath.parent.mkdir(0o755)
    if resultpath.exists():
        jeez = json.load(resultpath.open()) or []
    else:
        jeez = []
    jeez.append(output)
    resultpath.write_text(json.dumps(jeez))
    return url


if __name__ == '__main__':
    grabbed = pasteit()
    if not grabbed:
        sys.exit(0)
    # runcmd(f"echo {grabbed}|xsel -i -b")
    webbrowser.open(grabbed)
    print(grabbed)
