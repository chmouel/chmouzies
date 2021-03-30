#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chmouel Boudjnah <chmouel@chmouel.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import argparse
import json
import os
import subprocess
import sys
import tempfile


def get_goobook_json():
    cmd = "goobook dump_contacts"
    goobook = subprocess.run(cmd,
                             shell=True,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE)
    if goobook.returncode != 0:
        print("i could not run '%s'" % (cmd))
        sys.exit(1)
    return json.loads(goobook.stdout.decode().strip())


def show_names():
    jeez = get_goobook_json()
    allnames = []
    for i in jeez:
        if 'names' in i:
            for names in i['names']:
                name = names['displayName']
                if name.startswith("+") or name[0].isdigit():
                    continue
                allnames.append(names['displayName'])
    allnames.sort()
    tmp = tempfile.NamedTemporaryFile(mode='w',
                                      delete=False,
                                      prefix="fzf-contact-")
    tmp.write("\n".join(allnames))
    tmp.close()
    cmdline = f"cat {tmp.name}|fzf -0 -n 1 -m -1"
    try:
        popo = subprocess.run(cmdline,
                              shell=True,
                              stdout=subprocess.PIPE,
                              check=True)
    except subprocess.CalledProcessError:
        return ""
    finally:
        os.remove(tmp.name)

    reply = popo.stdout.decode().strip()
    preview(reply)


def preview(name):
    cmdline = f"goobook dquery '{name}'"
    try:
        popo = subprocess.run(cmdline,
                              shell=True,
                              stdout=subprocess.PIPE,
                              check=True)
    except subprocess.CalledProcessError as error:
        print(error)
        return ""

    print(popo.stdout.decode().strip())
    answer = input("Copy (n)ame (e)mail (m)obile (a)addres")
    print(answer)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("function", nargs="?")
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()
    if args.function == "preview":
        preview(args.args)
    else:
        show_names()
