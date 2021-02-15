#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys

notify_me_on_inbox = re.compile("(.*(Personal|Work)-Inbox|.*0-GitHUB)")
only_show_inbox = re.compile(r".*")
remove_gmail_folder = True

DEBUG = False


def get_inbox_statuses():
    try:
        emacsclient_output = subprocess.run(
            "emacsclient --eval \"(my-is-there-any-mail-out-there-json)\"",
            stderr=subprocess.PIPE,
            shell=True,
            check=True,
            stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        if DEBUG:
            print(e)
        return {}

    return json.loads(
        (emacsclient_output.stdout.decode()[1:-2].replace('\\"', '"')))


def main():
    jeez = get_inbox_statuses()
    meself = os.path.realpath(__file__)
    if not jeez:
        print("⬛")
        return
    icon = "📪"
    ret = ["---"]
    for inbox, number in jeez.items():
        if remove_gmail_folder:
            inbox = inbox.split("/")[-1]
        if not only_show_inbox.match(inbox):
            continue
        if notify_me_on_inbox.match(inbox):
            icon = "💌"
        ret.append(
            f"{inbox} ({number}) | bash=\"{meself} {inbox}\" terminal=false")
    if len(ret) == 1:
        print("⬛")
        return
    ret.insert(0, f"{icon}")
    print("\n".join(ret))
    print("\n--\nRefresh | refresh=true")


def goto_inbox(inbox):
    subprocess.run(
        f"emacsclient --eval '(my-is-there-any-mail-out-there-focus-group \"{inbox}\")'",
        stderr=subprocess.PIPE,
        shell=True,
        check=True,
        stdout=subprocess.PIPE)
    subprocess.run("jumpapp -X emacs27",
                   stderr=subprocess.PIPE,
                   shell=True,
                   check=False,
                   stdout=subprocess.PIPE)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            goto_inbox(sys.argv[1])
        except subprocess.CalledProcessError:
            pass
    else:
        main()
