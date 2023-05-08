
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

datastore_client = datastore.Client()


def createDirectoryEntity(directory_name):

    entity_key = datastore_client.key('Directory', directory_name)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'name': directory_name,
        'subDirectories': [],
        'file_list': []
    })

    datastore_client.put(entity)

    return directory_name


def addDirectoryToUser(user_info, directory_name):
    directory_keys = user_info['directory_list']
    directory_keys.append(directory_name)
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


def retrieveDirectoryEntity(directory_name):
    entity_key = datastore_client.key('Directory', directory_name)
    entity = datastore_client.get(entity_key)
    return entity


def getFileList(directory_name):

    files = retrieveDirectoryEntity(directory_name)
    return files['file_list']


def deleteDirectoryEntity(user_info, directory_name):

    directory_list_keys = user_info['directory_list']

    directory_key = datastore_client.key(
        'Directory', directory_list_keys[directory_name])
    if directory_key['file_list'] != []:
        print("ERROR: Must be empty before deletion")
        return False

    datastore_client.delete(directory_key)

    del directory_list_keys[directory_name]

    user_info.update({
        'directory_list': directory_list_keys
    })
    datastore_client.put(user_info)

    return True
