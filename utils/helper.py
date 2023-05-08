import urllib.parse
from flask import Flask


def urlSafe(url):
    return urllib.parse.quote(url, safe="")


def parseSafeUrl(url):
    return urllib.parse.unquote(url)
