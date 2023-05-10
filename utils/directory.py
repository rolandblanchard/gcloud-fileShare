
import uuid
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteDirectoryBlob

from utils.helper import getEntityById

datastore_client = datastore.Client()


def createDirectoryEntity(user_id, directory_name):
    key = uuid.uuid4().hex
    entity_key = datastore_client.key('Directory', key)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'key': key,
        'user_id': user_id,
        'name': directory_name,
        'subDirectories': [],
        'file_list': [],
        'size': 0
    })

    datastore_client.put(entity)

    return key


def addDirectoryToUser(user_info, key):
    directory_keys = user_info['directory_list']
    directory_keys.append(key)
    user_info.update({
        'directory_list': directory_keys
    })
    datastore_client.put(user_info)


def retrieveDirectories(user_info):
    # make key objects out of all the keys and retrieve them
    directory_ids = user_info['directory_list']
    directory_keys = []
    for i in range(len(directory_ids)):
        directory_keys.append(datastore_client.key(
            'Directory', directory_ids[i]))

    directory_list = datastore_client.get_multi(directory_keys)
    return directory_list


def retrieveDirectoryEntity(user_info, directory_name):

    directories = retrieveDirectories(user_info)
    for entity in directories:
        if entity['name'] == directory_name:
            return entity

    return None


def getFileList(directory_name):

    files = retrieveDirectoryEntity(directory_name)
    return files['file_list']


def deleteDirectory(user_info, directory_name):

    if directory_name == 'root':
        return False

    directory_list = user_info['directory_list']

    directory = retrieveDirectoryEntity(user_info, directory_name)

    if directory['file_list'] != []:
        print("ERROR: Must be empty before deletion")
        return False

    datastore_client.delete(directory)

    directory_list.remove(directory_name)

    user_info.update({
        'directory_list': directory_list
    })

    datastore_client.put(user_info)

    deleteDirectoryBlob(directory_name)

    return True


def updateMemory(directory, file_size):
    current = int(directory['size']) + int(file_size)

    directory.update({
        'size': current
    })

    datastore_client.put(directory)


def collectMemory(user_info):
    directory_list = retrieveDirectories(user_info)
    sum = 0
    for directory in directory_list:
        sum += int(directory['size'])

    user_info.update({
        'size': sum
    })
    datastore_client.put(user_info)


def getSharingDirectory(user_email):
    collab_info = getEntityById('UserInfo', user_email)
    if collab_info == None:
        return None
    directories = retrieveDirectories(collab_info)
    for dir in directories:
        if dir['name'] == 'shared':
            return dir
    return None
