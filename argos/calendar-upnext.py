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
"""
Show next google calendar events in bitbar/argos

Inspired from another script and completely rewritten it.
"""
import datetime
import os.path
import re
import subprocess
import sys

import apiclient
import dateutil.parser as dtparse
import dateutil.relativedelta as dtrelative
import dateutil.tz as dttz
import httplib2
import tzlocal
from oauth2client.file import Storage

RESTRICT_TO_CALENDAR = ["Work"]
MY_EMAIL = "cboudjna@redhat.com"
MAX_LENGTH = 50
EVENT_ORGANIZERS_ICON = {
    "^Tekton$":
    "🐱",
    r"(pbhattac|nkakkar|rbehera|vdemeest|kbaig|pchandra|ssadeghi|hshinde|nikthoma|pthangad|yhontyk|varadhya|pgarg|pradkuma|sashture|sthaha|gmontero|ppitonak)@redhat.com":
    "👷"
}

# We assume that you use pass to store your secret in gpg
PASS_CREDENTIALS_ID = "google-calendar-api-token"
CREDENTIAL_PATH = os.path.expanduser(
    "~/.credentials/calendar-python-quickstart.json")
SKIP_NON_ACCEEPTED = True


def htmlspecialchars(text):
    """Replace html chars"""
    return (text.replace("&", "&amp;").replace('"', "&quot;").replace(
        "<", "&lt;").replace(">", "&gt;"))


def get_credentials():
    """Gets valid user credentials from storage.
    """
    ret = subprocess.run(f"pass show {PASS_CREDENTIALS_ID}",
                         shell=True,
                         check=True,
                         capture_output=True)
    if ret.returncode != 0:
        raise Exception(
            f"cmd: pass show {PASS_CREDENTIALS_ID} has failed :\\ ")
    # Stupid lib excpecting file
    with open(CREDENTIAL_PATH, 'w') as filepath:
        filepath.write(ret.stdout.decode())
    store = Storage(CREDENTIAL_PATH)
    return store.get()


def filter_relevent_events(events):
    """filter events making sure it's accepted and not past"""
    ret = []
    for event in events:
        if 'date' in event['start']:
            continue
        start_time = dtparse.parse(event['start']['dateTime']).astimezone(
            tzlocal.get_localzone())
        end_time = dtparse.parse(event['end']['dateTime']).astimezone(
            tzlocal.get_localzone())
        now = datetime.datetime.now(dttz.tzlocal()).astimezone(
            tzlocal.get_localzone())

        if now >= end_time:
            continue

        if 'attendees' not in event:
            continue

        # Get only accepted events
        skip_event = False
        if SKIP_NON_ACCEEPTED:
            skip_event = True
        for attendee in event['attendees']:
            if attendee['email'] == MY_EMAIL and attendee[
                    'responseStatus'] == "accepted":
                skip_event = False
        if skip_event:
            continue
        event['start']['dateTime'] = start_time
        ret.append(event)
    return ret


def first_event(event):
    """Show first even in toolbar"""
    summary = htmlspecialchars(event['summary'].strip()[:20])
    now = datetime.datetime.now(dttz.tzlocal()).astimezone(
        tzlocal.get_localzone())
    end_time = dtparse.parse(event['end']['dateTime']).astimezone(
        tzlocal.get_localzone())
    start_time = event['start']['dateTime']

    if now > start_time:
        _rd = dtrelative.relativedelta(end_time, now)
    else:
        _rd = dtrelative.relativedelta(start_time, now)
    humzrd = ""
    for dttype in (("day", _rd.days), ("hour", _rd.hours), ("minute",
                                                            _rd.minutes)):
        if dttype[1] == 0:
            continue
        humzrd += f"{dttype[1]} {dttype[0]}"
        if dttype[1] > 1:
            humzrd += "s"
        humzrd += " "
    if now > start_time:
        humzrd = humzrd.strip() + " left"
    return f"{humzrd.strip()} - {summary}"


def show(events):
    """Show all events in menuitems"""
    currentday = ""
    now = datetime.datetime.now(dttz.tzlocal()).astimezone(
        tzlocal.get_localzone())
    if len(events) == 0:
        return []

    ret = [
        f" <span>{first_event(events[0])}</span>| imageWidth=20 iconName=x-office-calendar"
    ]
    ret.append("---")
    ret.append("Chmou Next Meeting|size=14")
    ret.append("")
    ret.append("Refresh | refresh=true")
    ret.append("\n")

    for event in events:
        _cday = events[0]['start']['dateTime'].strftime('%A %d %B %Y')
        if _cday != currentday:
            ret.append(f"{_cday}|color='#E67C73'")
            ret.append("---")
            ret.append("\n")
            currentday = _cday

        summary = htmlspecialchars(event['summary'].strip())

        organizer = event['organizer'].get('displayName',
                                           event['organizer'].get('email'))

        icon = "•"
        for regexp in EVENT_ORGANIZERS_ICON:
            if re.match(regexp, organizer):
                icon = EVENT_ORGANIZERS_ICON[regexp]
                break

        start_time = event['start']['dateTime']
        start_time_str = start_time.strftime("%H:%M")
        if now >= start_time:
            summary = f"<span color='blue'>{summary}</span>"

        href = ""

        if 'location' in event and event['location'].startswith("https://"):
            href = f"href={event['location']}"
        elif 'hangoutLink' in event:
            href = f"href={event['hangoutLink']}"
        ret.append(f"{icon} {summary} - {start_time_str} | {href}")

    return ret


def get_all_events(service):
    """Get all events from Google Calendar API"""
    page_token = None
    calendar_ids = []
    event_list = []
    while True:
        calendar_list = service.calendarList().list(
            pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if RESTRICT_TO_CALENDAR and calendar_list_entry[
                    'summary'] not in RESTRICT_TO_CALENDAR:
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
    api_service = apiclient.discovery.build('calendar',
                                            'v3',
                                            http=http_authorization)

    all_events = get_all_events(api_service)
    os.remove(CREDENTIAL_PATH)
    if not all_events:
        sys.exit(0)
    print("\n".join(show(all_events)))

# p(next_event['summary'])
