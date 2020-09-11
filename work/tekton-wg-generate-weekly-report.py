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
import os
import subprocess
from typing import Tuple

# pip3 install pygithub
import github

DEFAULT_REPOSITORY = "tektoncd/cli"
DAYS_FOR_REPORT = 7

DOC = """
      You need to have pygithub (pip3 install pygithub) installed.

      Github Tokens are needed are retrieved from your gitconfig in the github
      and variable oauth-token, set it like this: git config --global
      github.oauth-token THETOKEN.  you can override this with GITHUB_TOKEN
      environment variable.
      """


class Report:
    github_cnx = None

    def __init__(self, repository):
        self.get_token()
        self.repo = self.github_cnx.get_repo(repository)

    def get_token(self):
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            token = subprocess.Popen(
                ["git", "config", "--get", "github.oauth-token"],
                stdout=subprocess.PIPE).communicate()[0].strip().decode()

        if not token:
            raise Exception("Cannot find a github token")

        self.github_cnx = github.Github(token)

    def format_pr(self, pr):
        return f"{pr.title} - @{pr.user.login} - {pr.html_url}"

    def get_merged_prs(self) -> str:
        ret = ""
        for pr in self.repo.get_pulls(state='closed'):
            if datetime.datetime.now() - datetime.timedelta(
                    days=DAYS_FOR_REPORT) > pr.closed_at:
                break
            ret += self.format_pr(pr) + "\n"
        return ret

    def skip_it(self, pr) -> bool:
        for label in pr.labels:
            if label.name.startswith("do-not-merge"):
                return True
            elif label.name == "lifecycle/stale":
                return True
        return False

    def get_workingon_prs(self) -> Tuple[str, str]:
        ret = ""
        onhold = ""
        for pr in self.repo.get_pulls(state='open'):
            if self.skip_it(pr):
                onhold += self.format_pr(pr) + "\n"
                continue
            ret += self.format_pr(pr) + "\n"
        return (ret, onhold)

    def p_section(self, label, section) -> None:
        if not section:
            return
        print(f"{label}:\n\n{section}\n")


def main():
    parser = argparse.ArgumentParser(
        epilog=DOC,
        description='Generate report for Tekton workign group (or others 😎).')

    parser.add_argument('repository',
                        nargs="?",
                        type=str,
                        default=DEFAULT_REPOSITORY,
                        help='Repository to generate for')
    args = parser.parse_args()

    r = Report(args.repository)
    workingon, onhold = r.get_workingon_prs()
    r.p_section("Merged", r.get_merged_prs())
    r.p_section("Working on", workingon)
    r.p_section("On hold", onhold)


if __name__ == '__main__':
    main()
