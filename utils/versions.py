import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity

datastore_client = datastore.Client()


def createVersionEntity(file):
    now = datetime.datetime.now()

    entity = datastore.Entity()
    entity.update({
        'name': file['name'],
        'format': file['format'],
        'date_added': file['date_added'],
        'path': file['path']
    })

    return entity


def addVersionToFile(old_file, version):
    now = datetime.datetime.now()
    file_versions = old_file['versions']

    file_versions.append(version)

    old_file.update({
        'versions': file_versions,
        'date_modified': now
    })
    datastore_client.put(old_file)


def checkIfVersion(file_list, file_name):
    if file_name in file_list:
        return True
    else:
        return False
