import uuid
import datetime
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import deleteFileBlob
from utils.directory import retrieveDirectoryEntity, updateMemory, getSharingDirectory
from utils.helper import getEntityById

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
        'owner': ""
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


def deleteFile(user_info, file_key):

    print(user_info, "~", file_key)

    file = getEntityById('File', file_key)
    print('dir of file: ', file)
    file_size = getAllFileMemory(file)

    file_path = file['path']
    directory_name = file_path.split('/')[-2]
    print('dir of file: ', directory_name)

    directory = retrieveDirectoryEntity(user_info, directory_name)

    # get file path to get directory

    file_list = directory['file_list']

    datastore_client.delete(file.key)

    file_list.remove(file_key)

    updated_size = int(directory['size']) - file_size

    directory.update({
        'file_list': file_list,
        'size': updated_size
    })

    datastore_client.put(directory)

    deleteFileBlob(file)

    # remove memory


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


def shareFile(user_info, file_key):
    print('in shareFile')
    file = getEntityById('File', file_key)
    sharing = retrieveDirectoryEntity(user_info, 'shared')
    if not fileKeyExists(sharing, file_key):
        addFileToDirectory(sharing, file_key)


''' adds file key to collaborators sharing directory list '''


def addCollaborator(user_email, file_key):
    print('in addCollab')
    collab_directory = getSharingDirectory(user_email)
    if collab_directory == None:
        return False
    if not fileKeyExists(collab_directory, file_key):
        addFileToDirectory(collab_directory, file_key)
        return True
    return False
