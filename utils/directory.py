
import uuid
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteDirectoryBlob

from utils.helper import getEntityById
from utils.versions import *
from utils.userInfo import getAllUsers

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


def getViewingDirectories(user_info):

    all_directories = retrieveDirectories(user_info)
    viewing = []
    for dirs in all_directories:
        print('\n', dirs['name'], '\n')
        if str(dirs['name']) != 'shared' and str(dirs['name']) != str(user_info['user_id']):
            viewing.append(dirs)
            print('added: ', dirs['name'])

    return viewing


def deleteFileKeysFromShared(file_key):
    users = getAllUsers()
    for user in users:
        shared = retrieveDirectoryEntity(user, 'shared')
        file_list = shared['file_list']
        if file_key in file_list:
            print('file key in file list')
            file_list.remove(file_key)
            shared.update({
                'file_list': file_list
            })
            datastore_client.put(shared)
