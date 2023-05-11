import uuid
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.bucket import *
from utils.directory import *
from utils.helper import getEntityById
from utils.file import *
from utils.versions import *
from utils.userInfo import getUserInfoByEmail

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

        previous_version = createVersionEntity(file_blob)

        addVersionToFile(file_added, file_found, previous_version)

        # moveFileToVersion(file_found)
    else:

        id = createFileEntity(
            user_info, filename, directory['key'], directory_name, file_added)

        addFileToDirectory(directory, id)

    return file_size


def uploadFromShared(file_owner, file_key, file):

    original_file = getEntityById('File', file_key)
    print(str(file.filename), original_file['name'])

    if str(file.filename) == original_file['name']:

        print('\nFile versions match\n')

        original_directory = getEntityById('Directory', original_file['root'])

        print("\nadding file version from sharing: ", file_owner, '\n')

        collab_info = getUserInfoByEmail(file_owner)

        directory_name = collab_info['user_id'] + '/'

        if original_directory['key'] != collab_info['root_key']:
            directory_name = directory_name + original_directory['name']+'/'

        file_added = addFileBlob(file, directory_name)

        file_size = file_added.size

        # create version from old_file
        file_blob = getPreviousVersion(original_file, file_added.generation)

        previous_version = createVersionEntity(file_blob)

        addVersionToFile(file_added, original_file, previous_version)

        updateMemory(original_directory, file_size)

    else:
        print('\nFile must match version\n')


def deleteFile(user_info, file_key):

    file = getEntityById('File', file_key)

    file_size = getAllFileMemory(file)

    file_path = file['path']
    directory_name = file_path.split('/')[-2]

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

    deleteFileKeysFromShared(file_key)

    deleteFileBlob(file)


def shareFile(user_info, file_key):

    file = getEntityById('File', file_key)
    sharing = retrieveDirectoryEntity(user_info, 'shared')
    if not fileKeyExists(sharing, file_key):
        addFileToDirectory(sharing, file_key)


def getSharedFiles(user_info):
    owned_list = []
    collab_list = []

    shared = retrieveDirectoryEntity(user_info, 'shared')
    print('\nsearching for shared files...')
    if len(shared['file_list']) > 0:
        for key in shared['file_list']:
            file = getEntityById('File', key)
            if file['owner'] == user_info['email']:
                print('\nadded owned:', file['owner'], '\n')
                owned_list.append(file)
            else:
                collab_list.append(file)
    else:
        print('\nShared Folder empty\n')

    return owned_list, collab_list


''' adds file key to collaborators sharing directory list '''


def addCollaborator(user_email, file_key):
    print('\nin addCollab')
    collab_directory = getSharingDirectory(user_email)
    if collab_directory == None:
        print('Directory not found\n')
        return False
    print('Directory found\n')
    if not fileKeyExists(collab_directory, file_key):
        print('filekey new\n')
        addFileToDirectory(collab_directory, file_key)
        return True

    print('filekey exists\n')

    return False
