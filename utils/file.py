import uuid
import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity
from utils.helper import getEntityById

datastore_client = datastore.Client()


def createFileEntity(user_id, file_name, path, file_blob):
    key = uuid.uuid4().hex
    format = file_name.split(".")[-1]
    entity_key = datastore_client.key('File', key)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'key': key,
        'user_id': user_id,
        'name': file_name,
        'format': format,
        'versions': [],
        'current_version': "",
        'date_added': file_blob.time_created,
        'last_modified': file_blob.time_created,
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


def deleteFile(user_info, file_key):

    print(user_info, "~", file_key)

    file = getEntityById('File', file_key)
    print('dir of file: ', file)

    file_path = file['path']
    directory_name = file_path.split('/')[-2]
    print('dir of file: ', directory_name)

    directory = retrieveDirectoryEntity(user_info, directory_name)

    # get file path to get directory

    print(directory)

    file_list = directory['file_list']

    datastore_client.delete(file.key)

    file_list.remove(file_key)

    directory.update({
        'file_list': file_list
    })

    datastore_client.put(directory)

    deleteFileBlob(file)


def findFile(directory, file_name):
    files = retrieveFileEntities(directory)

    for file in files:
        if file['name'] == file_name:
            return file

    return None
