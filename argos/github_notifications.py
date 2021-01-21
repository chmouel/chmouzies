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
import datetime
import http.client
import json
import os
import re
import subprocess
import sys
import urllib
from itertools import groupby

import dateutil.parser

# TODO(chmou): handle support for github enteprise
GITHUB_URL = 'https://api.github.com'

# Configure these variables TIMESPAN and DAYSPAN to your liking
TIMESPAN = ("08h30", "18h30")
DAYSPAN = ("Mon", "Tue", "Wed", "Thu", "Fri")

# This will use the env variable and if that cannot be found it will try to get
# the token from the github.oauth-token section in your gitconfig
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


class Tools():
    @staticmethod
    def get_dict_subset(thedict, *keys):
        return dict([(key, thedict[key]) for key in keys if key in thedict])

    @staticmethod
    def github_request(url, /, method="GET", body=None, asjson=False):
        """Execute a request to the GitHUB API, handling redirect"""
        global GITHUB_TOKEN

        if not GITHUB_TOKEN:
            GITHUB_TOKEN = Tools.execute(
                "git config --get github.oauth-token").stdout.decode().strip()
        if GITHUB_TOKEN == "":
            raise Exception("No token has been defined in github.oauth-token")

        url_parsed = urllib.parse.urlparse(url)
        body = body and json.dumps(body)
        conn = http.client.HTTPSConnection(url_parsed.hostname)
        conn.request(method,
                     url_parsed.path,
                     body=body,
                     headers={
                         "User-Agent": "ChmouNotifications",
                         "Authorization": "Bearer " + GITHUB_TOKEN,
                     })
        response = conn.getresponse()
        if response.status == 301:
            return Tools.github_request(method, response.headers["Location"])

        if asjson:
            return json.load(response)
        return response

    @staticmethod
    def format_notification(notification):
        notification_type = notification['subject']['type']
        formatted = {
            'thread':
            notification['url'],
            'title':
            notification['subject']['title'],
            'href':
            notification['subject']['url'],
            'image':
            'iVBORw0KGgoAAAANSUhEUgAAAA4AAAAQCAYAAAAmlE46AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEwAACxMBAJqcGAAAA',
        }
        if len(formatted['title']) > 90:
            formatted['title'] = formatted['title'][:79] + '…'

        formatted['title'] = formatted['title'].replace('|', '-')
        latest_comment_url = notification.get('subject',
                                              {}).get('latest_comment_url',
                                                      None)
        typejson = Tools.github_request(formatted['href'], asjson=True)
        if latest_comment_url:
            formatted['href'] = (Tools.github_request(latest_comment_url, asjson=True) or {}).get('html_url', formatted['href'])

        if formatted['href']:
            formatted['href'] = re.sub(
                r'api\.|api/v3/|repos/', '',
                re.sub('(pull?|commit)s', r'\1', formatted['href']))
        if notification_type == 'PullRequest':
            if typejson and typejson['merged']:
                formatted[
                    'image'] += 'SpJREFUKJG9kkFOwmAQhb+ZQiVx5xm4hIlncEF7jLZuWSjSeAJsvQUY4xkMHsCtcU9MXBmwJsy4EWgFEt34VpP55mX+eflhj9KoGO5jAK00LmOwoZiaYIPRbXaXRsVQRC6BvWZJ4uLJRI6DcKlUMsVl/G0CwIw3UR8V4+QKxFd9BbfDqiP6buo1sB5QjgTJ07i8aPTFgvNFa/7i7fYzaL+YpEN3zwGux4mY2QmAm6db783i0rO4bGyrh7OL66a0Bigm6d5gGkYz3brvV8a/SjeF/dPGJLrpmTMDXs/i4vTnQNYrInNm5szqvIVYbiJdCV1Z6ANwXze6em4i3SBcqi+CNVeAIFxq9dkR0+07HfHVz6rzlsLAK5keUCEu/R0hDD7C+SME6A7+Z30BqF2G+GPLjSUAAAAASUVORK5CYII='
            elif typejson and typejson['state'] == 'closed':
                formatted[
                    'image'] += 'Q9JREFUKJG9kjFOw0AQRd9sbAiiQOIMqWJfAInOPULANehTQIjFCbgHFS1eKhR6cDpEbyHRmljyDpWVTWJbSsOvRvvm72i+BjpkI2ZdDIBszNVzTG7HvGcx543JxmifT7KIj4FyUlaYcMjcKI8Id17Pj8JDknMvrD4zoriwRg4OMaKtU44FUhtz6z8aFW7KkC9X82mESbJghpICJDkiyimAwvV2EDG6uZMfThs3TeFYB8miP1XjFb0pdhp31cro/muijbjAUTjDtx1zttnwEnGJo8BR+DxQSAcwWv5i9vd4BZ58Yy2kgTIqq3VuAMoKEx4htCQrijaX5fMAYRoOmbMEJ0y2lhGmZcgbNdDGd9Uf3M1iNlKZZGMAAAAASUVORK5CYII='
            else:
                formatted[
                    'image'] += 'TJJREFUKJG9krFOAlEQRe/MLpqHnd/ATyBWsLWF+hcLPYXibvwCE/gLC2MNVrD7AbbGnpjYboBlro2QXWATabzVy5x338ydPKBC4awTVTEA8Huz9i1FI5gZBINh6+0lnHUiEXkAUGmWMGm/c7Fues4pLU9IPv+aAABm9i2qT6Pm+BECbuoqpnZWW4lmmRLG3ZdV9VyAOEyD+1JdVO4yqX+ua7UPofRHrUlEMgaA4cVYALkEACF6e/N2k4DdJCh1Ky7nENftyVACo9akcjElox3I9yfjsdoaVfFPHbtpcG2GOUy/wjS42r0QTjs3ZpibYV7kPmkxVuuGOKfIl1MAr0WjqMRcrBqec8oCVwDwnNOFnwugezkJ4+ZnFbkPeANanpwsAQr7+2m8Qab1FKcAeYgfqR/3P4pMOYR15QAAAABJRU5ErkJggg=='
            if typejson and typejson.get('user', {}).get('login', None):
                formatted['title'] += ' (by @{})'.format(
                    typejson['user']['login'])
        elif notification_type == 'RepositoryInvitation':
            formatted[
                'image'] = 'iVBORw0KGgoAAAANSUhEUgAAAA4AAAAKCAYAAACE2W/HAAAAAXNSR0IArs4c6QAAAM1JREFUKBWVkD0OQUEUhcdv/ASJn55SyxLoVBJq8tZjBRQsgkZiAQoqOiQ2oFc935nMvLxEXsRJPufOufe+kTHGmBeEf3Jg3i4t8IwOP6QZzeoi+3PFt1BRkKAq+Q4uEKbdUA+/wxm6LoubshPcoO8b9lp3GOMPGPomPoInqOcV/VUfyKfwhsChegJxfS3O6R5hALpFqFY2A69osUyygT3UQOpAWwVSpt4aShAt6lWXkIUk5WiswL5qiqIODdBz6+ZirM67cwFvulwfaH0AC7M1lHL62U4AAAAASUVORK5CYII='
            formatted['templateImage'] = formatted.pop('image')
            formatted['href'] = 'https://github.com/{}/invitations'.format(
                notification['repository']['full_name'])
        elif notification_type == 'Issue':
            if typejson and typejson['state'] == 'closed':
                formatted[
                    'image'] += 'YpJREFUKJGdkj9I23EQxT93SZrJQYNQ6Bo65BtQcHRpSeyUuQqNWx2ti7qJRpqhUxGX0lGhlXQ0uJhfU7cOLm3+QKCzoIjoJpp8z0HT/BpJBd90HO/dvTsePBLS36iM8Uw6vANyQNJ7RJU/wG7nmo1XLY7uCStp8uL5BJwgbJtRU8E8jImR98qoGHPZBjsSFhlsCRQjCQovD2iHhx5OEDu/ZF2E5Y4wLn/tXdMy5WO2zkqXHKQxgEy95+y7Y1KMXwogbeaBk0iCwqBn7DteAJym+NmBnSiAF3IK2/32wiIVqoGjYE1GRMlGARSSZtQGbZtq8CNwFBBWDUxgJjqI3I9Mg7XAgRoXmSYlACqOWuAG39ePimNB7+oyxuzhBLEwIUhj3c92sZckLsaSAvg2m14ZPb98eGs8ThFlqBcAx4wJX8T4cGasvm5yFRaUUjwZUd4bLKow/W/kbsWfgTMxvorxmwhtjHEPbxSGEd5many7F/JqiqdemceT88rzu3ZLoWywma1z/NA5/8UNNkSJCdaYQF4AAAAASUVORK5CYII='
            else:
                formatted[
                    'image'] += 'ZxJREFUKJGdkjFoU2EUhb97k9jNRzEFoWvJVHXoZCqIaQaH7JaUbtpi2zc4ORWJYKGTYJLBroFaiGPo0hBwyAOhU51Cd8EOOid53uugL4SnkOK3/dx7OPccfvhPZPqxHZUWc0gIUjFs6c/CJdDBtN580P36lzCM1jZ+mr9HuFKkJfgXABO9i/mmqOTd7VlztXcyEYbR2oabtFx5kx+Oa7VHn+LpS7bOV3K5UfBaTF+6WLW52juR7ai0mDEGovq2WezuJ8t7UdkBGsXu5KqdfvlQhOeeGRc0h4QIV/nhuDarkIVgft+xHxJnQwWpKNJKn/cvasvtkcCxuFTUsKWkiOsgrhcoBb2uIE1W4NKRO8DH6cF0KSnLewYDBTqGb26dr+Sm53tR2ZNmE8LTx3O4V9XpKKZ1FV24MZyf2aoH8YE5garXBWC3X1oX12NXO8zfvPWqttwepZ08iA9wXqDypFE8a09y7PZL64geCXx37IO4XiSZcK/+dso8bRTP2pD65DufH96WOBuKSwWlAGD4QJ2Oqtff3e99mxVnJr8AXSGi02ni0+YAAAAASUVORK5CYII='
        elif notification_type == 'Commit':
            formatted[
                'image'] += 'HhJREFUKJHl0LEKwkAQBNCH3yIaf05S+VUqmh8ykFoUYn8WbnEc8a7XgYVlmNkdhv/EDgNmvHDFtmXq8ETCiFvsD2xqxksI9xnXB3cqxamYceHgVOpWC6JUi/QNQxj7jDsEd6wZ83KmLOId69bXzqekOeas0eiv4g3q4SY7NY1R2gAAAABJRU5ErkJggg=='
            formatted['templateImage'] = formatted.pop('image')
        elif notification_type == 'Release':
            formatted[
                'image'] += 'JdJREFUKJGl0DsKwkAUBdDTRgvFHbgmNyLY+QWzKxM/kK2kSKc70MIIQ0ziqBceA/dxinn8mSkKVMGUmH+CBWaNboQjdn2wqt97Pa8kNd5+C0O86YNdSZC34RLjCJxhHZYLXDCIxKuwTHGOwBNcm2WKUw9OcMCybZl6XjHpQOs30cB5gKNQiDPPP0WjV/a4aVwxNsNfUGce7P8k4XgVPSYAAAAASUVORK5CYII='
            formatted['templateImage'] = formatted.pop('image')
        return formatted

    @staticmethod
    def print_notifications(notifications):
        notifications = sorted(
            notifications,
            key=lambda notification: notification['repository']['full_name'])
        for repo, repo_notifications in groupby(
                notifications,
                key=lambda notification: notification['repository']['full_name'
                                                                    ]):
            if repo:
                repo_notifications = list(repo_notifications)
                # Tools.print_bitbar_line(title=repo)
                # Tools.print_bitbar_line(
                #     title='{title} - Mark {count} As Read'.format(
                #         title=repo, count=len(repo_notifications)),
                #     # alternate='true',
                #     refresh='true',
                #     bash=__file__,
                #     terminal='false',
                #     param1='readrepo',
                #     param2=repo)
                for notification in repo_notifications:
                    formatted_notification = Tools.format_notification(
                        notification)
                    Tools.print_bitbar_line(refresh='true',
                                            **Tools.get_dict_subset(
                                                formatted_notification,
                                                'title', 'href', 'image',
                                                'templateImage'))
                    # Tools.print_bitbar_line(
                    #     refresh='true',
                    #     title='%s - Mark As Read' %
                    #     formatted_notification['title'],
                    #     # alternate='true',
                    #     bash=__file__,
                    #     terminal='false',
                    #     param1='readthread',
                    #     param2=formatted_notification['thread'],
                    #     **Tools.get_dict_subset(formatted_notification, 'image', 'templateImage'))

    @staticmethod
    def plural(word, number):
        return str(number) + ' ' + (word + 's' if number > 1 else word)

    @staticmethod
    def print_bitbar_line(title, **kwargs):
        print(f'{title} | ' + (' '.join([f'{k}={v}' for k, v in kwargs.items()])))

    @staticmethod
    def execute(command, check_error=""):
        """Execute a commmand"""
        result = ""
        try:
            result = subprocess.run(['/bin/sh', '-c', command],
                                    stdout=subprocess.PIPE,
                                    check=True)
        except subprocess.CalledProcessError as exception:
            if check_error:
                print(check_error)
                raise exception
        return result


class GithubNotifications():
    color_active = '#4078C0'
    color_inactive = '#7d7d7d'

    def main(self, sysargs):
        parser = argparse.ArgumentParser()
        parser.add_argument("--readrepo", action='store_true',
                            default=False)
        parser.add_argument("--readthread", action='store_true',
                            default=False)
        parser.add_argument("others", nargs="*", default="")
        args = parser.parse_args(sysargs)

        if args.readrepo:
            self.readrepo(args.others[0])
        elif args.readthread:
            self.readthread(args.others[0])
        elif datetime.datetime.now().strftime("%a") not in DAYSPAN:
            print("🏖️")
        elif (datetime.datetime.now() < dateutil.parser.parse(TIMESPAN[0]) or
              datetime.datetime.now() > dateutil.parser.parse(TIMESPAN[1])):
            print("🛌")
        else:
            self.get_notifications()

    def readrepo(self, repo):
        print(f'Marking repo {repo} as read')
        url = f'{GITHUB_URL}/repos/{repo}/notifications'
        Tools.github_request(url, method="PUT", body={})

    def readthread(self, url):
        print(f'Marking thread {url} as read')
        Tools.github_request(url, method="PATCH", body={})

    def get_notifications(self):
        notifications = json.load(Tools.github_request(GITHUB_URL + "/notifications"))

        if notifications:
            Tools.print_bitbar_line(title='🔵', color=self.color_active)
            print('---')
        else:
            print('⦿')
            sys.exit(0)

        Tools.print_bitbar_line(title='Refresh', refresh='true')

        if notifications:
            Tools.print_bitbar_line(
                title=(u'GitHub \u2014 %s' %
                       Tools.plural('notification', len(notifications))),
                color=self.color_active,
                href='https://github.com/notifications',
            )
            Tools.print_notifications(notifications)
        else:
            Tools.print_bitbar_line(
                title=u'GitHub \u2014 No new notifications',
                color=self.color_inactive,
                href='https://github.com',
            )


if __name__ == '__main__':
    gh_notif = GithubNotifications()
    gh_notif.main(sys.argv[1:])
