import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity

datastore_client = datastore.Client()


def createFileEntity(file_name, path):
    now = datetime.datetime.now()
    format = file_name.split(".")[-1]
    entity_key = datastore_client.key('File', file_name)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'name': file_name,
        'format': format,
        'versions': [],
        'date_added': now,
        'last_modified': now,
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


def retrieveFileEntities(directory):

    file_ids = directory['file_list']
    file_keys = []
    for i in range(len(file_ids)):
        file_keys.append(datastore_client.key(
            'File', file_ids[i]))

    file_list = datastore_client.get_multi(file_keys)
    return file_list


def getFileEntity(file_name):
    entity_key = datastore_client.key('File', file_name)
    entity = datastore_client.get(entity_key)
    return entity


def deleteFile(file_name):

    # get file path to get directory
    file = getFileEntity(file_name)
    file_path = file['path']

    directory = retrieveDirectoryEntity(file_path)
    print(directory)

    file_list = directory['file_list']

    file_key = datastore_client.key(
        'File', file_name)
    print(file_key)

    datastore_client.delete(file_key)

    file_list.remove(file_name)

    directory.update({
        'file_list': file_list
    })

    datastore_client.put(directory)

    deleteFileBlob(file_path, file_name)


def deleteFileEntity(directory, file_name):

    file_list = directory['file_list']

    file_key = datastore_client.key(
        'File', file_name)

    datastore_client.delete(file_key)

    file_list.remove(file_name)

    directory.update({
        'file_list': file_list
    })
    datastore_client.put(directory)

    return True
