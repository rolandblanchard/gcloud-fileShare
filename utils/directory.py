
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response


app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


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


def retrieveDirectoryEntity(user_info):
    # make key objects out of all the keys and retrieve them
    directory_ids = user_info['directory_list']
    directory_keys = []
    for i in range(len(directory_ids)):
        directory_keys.append(datastore_client.key(
            'Directory', directory_ids[i]))

    directory_list = datastore_client.get_multi(directory_keys)
    return directory_list
