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


parser = argparse.ArgumentParser()
parser.add_argument("pod", nargs="+", default=False)
args = parser.parse_args(sys.argv[1:])

for pod in args.pod:
    shell = subprocess.run(
        # "cat /tmp/a.json".split(" "),
        ("oc get pod -ojson %s" % (pod)).split(" "),
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    if shell.returncode != 0:
        print("The was some problem running oc get pod on %s" % (pod))
        sys.exit(1)

    output = shell.stdout.decode().strip()
    jeez = json.loads(output)
    for container in jeez['status']['containerStatuses']:
        state = list(container['state'].keys())[0].capitalize()

        if state == "Running":
            state = colourText(state, "green")
        elif state == "Terminated":
            state = colourText(state, "blue")

        lastlog = subprocess.run(
            ("oc logs --tail=1 %s -c%s" % (pod, container['name'])).split(" "),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        if lastlog.returncode != 0:
            print(
                "i could not run oc logs on %s/%s" % (pod, container['name']))
            sys.exit(1)
        log = lastlog.stdout.decode().strip()
        if log:
            log = " - %s" % (log)
        print("[%s] - %s%s" % (colourText(container['name'], 'white_bold'),
                               state, log))
