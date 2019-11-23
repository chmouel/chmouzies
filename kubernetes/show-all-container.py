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
import sys
import subprocess
import json
import re


def colourText(text, color):
    colours = {
        'red': "\033[1;31m",
        'title': "\033[4;40m",
        'yellow': "\033[1;33m",
        'blue': "\033[1;34m",
        'blue_reverse': "\033[1;44m",
        'cyan': "\033[1;36m",
        'cyan_surligned': "\033[4;36m",
        'cyan_italic': "\033[3;37m",
        'green': "\033[1;32m",
        'grey': "\033[1;30m",
        'magenta_surligned': "\033[4;35m",
        'magenta': "\033[1;35m",
        'white': "\033[1;37m",
        'white_bold': "\033[1;40m",
        'reset': "\033[0;0m",
    }
    s = f"{colours[color]}{text}{colours['reset']}"
    return s


def show_log(kctl, args, container, pod):
    cmd = "%s logs --tail=%s %s -c%s" % (kctl, args.maxlines, pod, container)
    lastlog = subprocess.run(
        cmd.split(" "), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if lastlog.returncode != 0:
        print("i could not run '%s'" % (cmd))
        sys.exit(1)
    return lastlog.stdout.decode().strip()


def overcnt(jeez, kctl, pod, args):
    for container in jeez:
        if args.restrict:
            if len(re.findall(args.restrict, container['name'])) == 0:
                continue

        state = list(container['state'].keys())[0].capitalize()
        if state in "Running":
            state = colourText(state, "blue")
        elif state == "Terminated":
            if container['state']['terminated']['exitCode'] != 0:
                state = colourText("Fail", "red")
            else:
                state = colourText("Success", "green")
        elif state == "Waiting":
            state = colourText(state, "grey")

        cname = colourText(container['name'], 'white_bold')

        line_new = ' {:60}  {:>20}'.format(cname, state)
        print(line_new)

        if args.showlog:
            outputlog = show_log(kctl, args, container['name'], pod)
            if outputlog:
                print()
                print(outputlog)
                print()


parser = argparse.ArgumentParser()
parser.add_argument("pod", nargs="?", default="")
parser.add_argument('-n', dest="namespace", type=str)
parser.add_argument(
    '-r',
    '--restrict',
    type=str,
    help='Restrict to show only those containers (regexp)')

parser.add_argument(
    '-l',
    '--showlog',
    action='store_true',
    default=False,
    help='Show logs of containers')
parser.add_argument(
    '--maxlines',
    type=str,
    default="-1",
    help='Maximum line when showing logs')

args = parser.parse_args(sys.argv[1:])

kctl = 'kubectl'
if args.namespace:
    kctl += f" -n {args.namespace}"

if not args.pod:
    import os
    runcmd = f"{kctl} get pods -o name|fzf -1"
    args.pod = [os.popen(runcmd).read().strip().replace("pod/", "")]

for pod in args.pod:
    cmdline = f"{kctl} get pod {pod} -ojson"
    shell = subprocess.run(
        # "cat /tmp/a.json".split(" "),
        cmdline.split(" "),
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)
    if shell.returncode != 0:
        print("The was some problem running '%s'" % (cmdline))
        sys.exit(1)

    output = shell.stdout.decode().strip()
    jeez = json.loads(output)
    print("Init Containers: ")
    overcnt(jeez['status']['initContainerStatuses'], kctl, pod, args)
    print()
    print("Containers: ")
    overcnt(jeez['status']['containerStatuses'], kctl, pod, args)
