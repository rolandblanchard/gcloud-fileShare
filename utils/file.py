import uuid
import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response


datastore_client = datastore.Client()


def createFileEntity(user_info, file_name, root, path, file_blob):
    key = uuid.uuid4().hex
    format = file_name.split(".")[-1]
    user_id = user_info['user_id']
    owner = user_info['email']
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
        'root': root,
        'path': path,
        'size': file_blob.size,
        'owner': owner
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


def getAllFileMemory(file):
    sum = int(file['size'])
    for version in file['versions']:
        sum += int(version['size'])
    return sum


def findFile(directory, file_name):
    files = retrieveFileEntities(directory)

    for file in files:
        if file['name'] == file_name:
            return file

    return None


''' sends file key to sharing directory list'''


def fileKeyExists(directory, file_key):

    for dir in directory['file_list']:
        if dir == file_key:
            return True

    return False


def getUserInfoByEmail(email):

    query = datastore_client.query(kind='UserInfo')
    query.add_filter('email', '=', email)

    results = list(query.fetch(1))

    if not results:
        return None

    return results[0]
