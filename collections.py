#!/usr/bin/env python3
# coding: utf-8
import os
import sys
import json
import shutil
import logging
import argparse
import requests
import traceback
from lxml import html, etree
from html import escape
from random import random
from multiprocessing import Process, Queue, Value
from urllib.parse import urljoin, urlsplit, urlparse
import pickle

PATH = os.path.dirname(os.path.realpath(__file__))
COOKIES_FILE = os.path.join(PATH, "cookies.json")

ORLY_BASE_HOST = "oreilly.com"  # PLEASE INSERT URL HERE

SAFARI_BASE_HOST = "learning." + ORLY_BASE_HOST
API_ORIGIN_HOST = "api." + ORLY_BASE_HOST

ORLY_BASE_URL = "https://www." + ORLY_BASE_HOST
SAFARI_BASE_URL = "https://" + SAFARI_BASE_HOST
API_ORIGIN_URL = "https://" + API_ORIGIN_HOST

LOGIN_ENTRY_URL = SAFARI_BASE_URL + "/login/unified/?next=/home/"

url = "https://learning.oreilly.com/api/v2/collections/"

class Display:
    def __init__(self, log_file):
        self.last_request = (None,)

class Collections:

    HEADERS = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate",
            "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "cookie": "",
            "pragma": "no-cache",
            "origin": SAFARI_BASE_URL,
            "referer": LOGIN_ENTRY_URL,
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/60.0.3112.113 Safari/537.36"
        }

    def __init__(self):
        #self.name = name
        self.cookies = {}
        self.display = Display("")

        if not os.path.isfile(COOKIES_FILE):
            self.display.exit("Login: unable to find cookies file.\n"
                            "    Please use the --cred option to perform the login.")
        self.cookies = json.load(open(COOKIES_FILE))

    def return_cookies(self):
        return " ".join(["{0}={1};".format(k, v) for k, v in self.cookies.items()])

    def return_headers(self, url):
        if ORLY_BASE_HOST in urlsplit(url).netloc:
            self.HEADERS["cookie"] = self.return_cookies()

        else:
            self.HEADERS["cookie"] = ""

        return self.HEADERS

    def update_cookies(self, jar):
        for cookie in jar:
            self.cookies.update({
                cookie.name: cookie.value
            })

    def requests_provider(
        self, url, post=False, data=None, perfom_redirect=True, update_cookies=True, update_referer=True, **kwargs
):
        try:
            response = getattr(requests, "post" if post else "get")(
                url,
                headers=self.return_headers(url),
                data=data,
                allow_redirects=False,
                **kwargs
            )

            self.display.last_request = (
                url, data, response.status_code, "\n".join(
                    ["\t{}: {}".format(*h) for h in response.headers.items()]
                ), response.text
            )

        except (requests.ConnectionError, requests.ConnectTimeout, requests.RequestException) as request_exception:
            self.display.error(str(request_exception))
            return 0

        if update_cookies:
            self.update_cookies(response.cookies)

        if update_referer:
            # TODO Update Referer HTTP Header
            # TODO How about Origin? 
            self.HEADERS["referer"] = response.request.url

        if response.is_redirect and perfom_redirect:
            return self.requests_provider(response.next.url, post, None, perfom_redirect, update_cookies, update_referer)
            # TODO How about **kwargs?


        return response.json()

col = Collections()
content = col.requests_provider(url="https://learning.oreilly.com/api/v2/collections/")

json.dump(content[0], open('playlists.json', "w"))

# with open('playlists.json', 'wb') as output:
#     json.dump(content, output)