import urllib.parse
import uuid
import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity

datastore_client = datastore.Client()


def urlSafe(url):
    return urllib.parse.quote(url, safe="")


def parseSafeUrl(url):
    return urllib.parse.unquote(url)


def getEntityById(type, id):
    key = datastore_client.key(type, id)
    return datastore_client.get(key)
