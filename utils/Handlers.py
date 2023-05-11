import uuid
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import *
from utils.directory import *
from utils.helper import getEntityById
from utils.file import *
from utils.versions import *

datastore_client = datastore.Client()


def uploadFromDirectory(user_info, file, directory, key):
    filename = str(file.filename)

    directory_name = user_info['user_id'] + '/'

    if key != user_info['root_key']:
        directory_name = directory_name + directory['name']+'/'

    file_found = findFile(directory, filename)

    file_added = addFileBlob(file, directory_name)
    file_size = file_added.size

    if file_found != None:
        # create version from old_file
        file_blob = getPreviousVersion(
            file_found, file_added.generation)

        print('\ngeneration', file_blob.generation, "\ntime_created:",
              file_blob.time_created, "\nname:", file_blob.name)

        previous_version = createVersionEntity(file_blob)

        addVersionToFile(file_added, file_found, previous_version)

        # moveFileToVersion(file_found)
    else:

        id = createFileEntity(
            user_info, filename, directory['key'], directory_name, file_added)

        addFileToDirectory(directory, id)

    return file_size


def deleteFile(user_info, file_key):

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


def shareFile(user_info, file_key):
    print('in shareFile')
    file = getEntityById('File', file_key)
    sharing = retrieveDirectoryEntity(user_info, 'shared')
    if not fileKeyExists(sharing, file_key):
        addFileToDirectory(sharing, file_key)


def getSharedFiles(user_info):
    owned_list = []
    collab_list = []

    shared = retrieveDirectoryEntity(user_info, 'shared')
    print('\nsearching for shared files\n')

    for key in shared['file_list']:
        file = getEntityById('File', key)
        if file['owner'] == user_info['email']:
            owned_list.append(file)
        else:
            collab_list.append(file)

    return owned_list, collab_list


''' adds file key to collaborators sharing directory list '''


def addCollaborator(user_email, file_key):
    print('\nin addCollab\n')
    collab_directory = getSharingDirectory(user_email)
    if collab_directory == None:
        return False
    if not fileKeyExists(collab_directory, file_key):
        addFileToDirectory(collab_directory, file_key)
        return True
    return False
