import uuid
import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity

datastore_client = datastore.Client()


def createFileEntity(user_id, file_name, path):
    key = uuid.uuid4().hex
    now = datetime.datetime.now()
    format = file_name.split(".")[-1]
    entity_key = datastore_client.key('File', key)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'key': key,
        'user_id': user_id,
        'name': file_name,
        'format': format,
        'versions': [],
        'date_added': now,
        'last_modified': now,
        'path': path
    })

    datastore_client.put(entity)

    return key


def addFileToDirectory(directory, key):

    file_keys = directory['file_list']

    file_keys.append(key)
    directory.update({
        'file_list': file_keys
    })
    datastore_client.put(directory)


def retrieveFileEntities(directory):

    file_ids = directory['file_list']
    file_keys = []
    for i in range(len(file_ids)):
        file_keys.append(datastore_client.key(
            'File', file_ids[i]))

    file_list = datastore_client.get_multi(file_keys)
    return file_list


def getFileEntity(directory, file_name):

    files = retrieveFileEntities(directory)
    for entity in files:
        if entity['name'] == file_name:
            return entity

    return None


def deleteFile(user_info, file_name):

    directory = retrieveDirectoryEntity(user_info, file_path)

    # get file path to get directory
    file = getFileEntity(file_name)
    file_path = file['path']

    print(directory)

    file_list = directory['file_list']

    file_key = datastore_client.key(
        'File', file_name)

    datastore_client.delete(file_key)

    file_list.remove(file_name)

    directory.update({
        'file_list': file_list
    })

    datastore_client.put(directory)

    deleteFileBlob(file_path, file_name)
