from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response
app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


def createFileEntity(file_name, path):
    entity_key = datastore_client.key('File', file_name)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'name': file_name,
        'path': path
    })

    datastore_client.put(entity)

    return file_name


def addFileToDirectory(directory, file_name):
    file_keys = directory['file_list']
    file_keys.append(file_name)
    directory.update({
        'file_list': file_keys
    })
    datastore_client.put(directory)


def retrieveFileEntity(directory):

    file_ids = directory['file_list']
    file_keys = []
    for i in range(len(file_ids)):
        file_keys.append(datastore_client.key(
            'File', file_ids[i]))

    file_list = datastore_client.get_multi(file_keys)
    return file_list
