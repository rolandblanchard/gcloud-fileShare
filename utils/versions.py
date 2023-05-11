import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response


datastore_client = datastore.Client()


def createVersionEntity(fileBlob):
    now = datetime.datetime.now()

    entity = datastore.Entity()
    entity.update({
        'name': fileBlob.name,
        'time_created': fileBlob.time_created,
        'path': "",
        'version_of': "",
        'generation': fileBlob.generation,
        'size': fileBlob.size
    })

    return entity


def addVersionToFile(file_added, old_file, version):

    version.update({
        'path': old_file['path'],
        'version_of': old_file['key']
    })

    file_versions = old_file['versions']

    file_versions.append(version)

    old_file.update({
        'versions': file_versions,
        'current_version': file_added.generation,
        'last_modified': file_added.time_created
    })
    datastore_client.put(old_file)


def deleteVersionEntity(file, generation):
    size = 0
    for version in file['versions']:

        if version['generation'] == int(generation):

            size = int(version['size'])
            file['versions'].remove(version)
            datastore_client.put(file)
            return size
    return size
