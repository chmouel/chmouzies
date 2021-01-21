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
import datetime
import os.path

import dateutil.parser as dtparse
import dateutil.relativedelta as dtrelative
import dateutil.tz as dttz
import httplib2
import tzlocal
from oauth2client.file import Storage
import apiclient

RESTRICT_TO_CALENDAR = ["Work"]
MY_EMAIL = "cboudjna@redhat.com"
MAX_LENGTH = 50


def htmlspecialchars(text):
    """Replace html chars"""
    return (text.replace("&", "&amp;").replace('"', "&quot;").replace(
        "<", "&lt;").replace(">", "&gt;"))


def get_credentials():
    """Gets valid user credentials from storage.
    """
    credential_path = os.path.expanduser(
        "~/.credentials/calendar-python-quickstart.json")
    if not os.path.exists(credential_path):
        raise Exception("No credentials path")
    store = Storage(credential_path)
    return store.get()


def filter_relevent_events(events):
    """filter events making sure it's accepted and not past"""
    ret = []
    for event in events:
        if 'date' in event['start']:
            continue
        event_time = dtparse.parse(event['start']['dateTime']).astimezone(
            tzlocal.get_localzone())
        now = datetime.datetime.now(dttz.tzlocal()).astimezone(
            tzlocal.get_localzone())

        if now > event_time:
            continue

        # Get only accepted events
        skip_event = True
        for attendee in event['attendees']:
            if attendee['email'] == MY_EMAIL and attendee[
                    'responseStatus'] == "accepted":
                skip_event = False
        if skip_event:
            continue
        event['start']['dateTime'] = event_time
        ret.append(event)
    return ret


def first_event(event):
    summary = htmlspecialchars(event['summary'].strip()[:20])
    now = datetime.datetime.now(dttz.tzlocal()).astimezone(
        tzlocal.get_localzone())

    _rd = dtrelative.relativedelta(event['start']['dateTime'], now)
    humzrd = ""
    for dttype in (("day", _rd.days), ("hour", _rd.hours), ("minute",
                                                            _rd.minutes)):
        if dttype[1] == 0:
            continue
        humzrd += f"{dttype[1]} {dttype[0]}"
        if dttype[1] > 1:
            humzrd += "s"
        humzrd += " "
    return f"{humzrd.strip()} - {summary}"


def show(events):
    if len(events) == 0:
        return

    ret = [f":date: <span>{first_event(events[0])}</span>"]
    ret.append("---")
    ret.append("Chmou Next Meeting|size=14")
    ret.append("")
    ret.append("January 21, 2021|color='#E67C73'")
    count = 1

    for event in events:
        summary = htmlspecialchars(event['summary'].strip())
        timestr = event['start']['dateTime'].strftime("%H:%M")

        href = ""

        if 'location' in event and event['location'].startswith("https://"):
            href = f"href={event['location']}"
        elif 'hangoutLink' in event:
            href = f"href={event['hangoutLink']}"
        ret.append(f"{count}) {summary} - {timestr} | {href}")
        count += 1
    return ret


def get_all_events(service):
    page_token = None
    calendar_ids = []
    event_list = []
    while True:
        calendar_list = service.calendarList().list(
            pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] not in RESTRICT_TO_CALENDAR:
                continue
            calendar_ids.append(calendar_list_entry['id'])
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    for calendar_id in calendar_ids:
        uhy = service.events().list(calendarId=calendar_id,
                                    timeMin=now,
                                    maxResults=5,
                                    singleEvents=True,
                                    orderBy='startTime').execute()
        uhx = uhy.get('items', [])
        event_list = event_list + uhx

    event_list.sort(
        key=lambda x: x['start'].get('dateTime', x['start'].get('date')))

    return filter_relevent_events(event_list)


if __name__ == '__main__':
    credentials = get_credentials()
    http_authorization = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('calendar',
                                        'v3',
                                        http=http_authorization)

    all_events = get_all_events(service)
    print("\n".join(show(all_events)))
    print("---")
# p(next_event['summary'])
