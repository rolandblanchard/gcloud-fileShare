import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity
from utils.file import retrieveFileEntities

datastore_client = datastore.Client()


def createVersionEntity(fileBlob):
    now = datetime.datetime.now()

    entity = datastore.Entity()
    entity.update({
        'name': fileBlob.name,
        'time_created': fileBlob.time_created,
        'path': "",
        'version_of': "",
        'generation': fileBlob.generation
    })

    return entity


def addVersionToFile(old_file, version):

    version.update({
        'path': old_file['path'],
        'version_of': old_file['key']
    })

    file_versions = old_file['versions']

    file_versions.append(version)

    old_file.update({
        'versions': file_versions,
        'current_version': version['generation'],
        'last_modified': version['time_created']
    })
    datastore_client.put(old_file)


def deleteVersionEntity(file, generation):

    for version in file['versions']:
        print('version-', version['generation'])
        if version['generation'] == int(generation):
            print('found')
            file['versions'].remove(version)
            datastore_client.put(file)
            return True
    return False
