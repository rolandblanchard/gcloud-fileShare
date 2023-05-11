import datetime
import random
import local_constants
import urllib.parse
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response, url_for, send_file

from utils.userInfo import *
from utils.directory import *
from utils.file import *
from utils.bucket import *
from utils.versions import *
from utils.helper import *
from utils.Handlers import *


app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


@app.route('/add_user', methods=['POST'])
def addUserHandler():
    id_token = request.cookies.get("token")
    error_message = None
    shared = None
    file_list = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            file_key = request.form['file_key']

            user_info = retrieveUserInfo(claims)

            collab_email = request.form['email']

            collab_user = getUserInfoByEmail(collab_email)

            print('\n collab user: ', collab_user, '\n')

            if collab_user == None:
                print('\nUser not found\n')
            else:
                print('\nUser found\n')
                addCollaborator(collab_email, file_key)

            owned_list, collab_list = getSharedFiles(user_info)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('share.html', user_data=claims, error_message=error_message, owned_list=owned_list, collab_list=collab_list)


@app.route('/enterShare', methods=['POST'])
def enterSharedHandler():
    id_token = request.cookies.get("token")
    error_message = None
    shared = None
    owned_list = []
    collab_list = []
    shared = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            owned_list, collab_list = getSharedFiles(user_info)

            shared = retrieveDirectoryEntity(user_info, 'shared')

        except ValueError as exc:
            error_message = str(exc)

    return render_template('share.html', user_data=claims, error_message=error_message, owned_list=owned_list, collab_list=collab_list, shared=shared)


@app.route('/share', methods=['POST'])
def moveToSharedDirectoryHandler():
    id_token = request.cookies.get("token")
    error_message = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            file_key = request.form['file_key']
            user_info = retrieveUserInfo(claims)

            shareFile(user_info, file_key)

        except ValueError as exc:
            error_message = str(exc)

    return redirect('/')


@app.route('/download/<filekey>/<generation>', methods=['POST'])
def downloadVersionHandler(filekey, generation):

    file = getEntityById('File', filekey)
    file_path = file['path']+file['name']

    # downloads the file formatting
    return Response(
        downloadBlobVersion(file_path, generation),
        mimetype='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment;filename={file["name"]}'
        }
    )


@app.route('/delete_version/<filekey>/<generation>', methods=['POST'])
def deleteVersioningHandler(filekey, generation):
    id_token = request.cookies.get("token")
    error_message = None
    directory = None
    file = None
    current_directory = ""
    version_count = 0
    version_list = []
    file_path = ""

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)

            file = getEntityById('File', filekey)

            directory = getEntityById('Directory', file['root'])
            current_directory = directory['name']

            versions = getBlobVersions(file)

            version_count = len(list(versions))

            version_list = file['versions']

            file_path = file['path']+file['name']
            print("deleting version entity- ", generation)

            updated_size = deleteVersionEntity(file, generation)

            if updated_size > 0:

                print("deleting blob version of size", updated_size)
                deleteBlobVersion(file_path, generation)
                updateMemory(directory, -updated_size)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('versions.html', user_data=claims, error_message=error_message, file=file, current_directory=current_directory, version_count=version_count, version_list=version_list)


@app.route('/versions/<file_id>', methods=['POST'])
def enterVersioningHandler(file_id):
    id_token = request.cookies.get("token")
    error_message = None
    directory = None
    file = None
    current_directory = ""
    version_count = 0
    version_list = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)

            file = getEntityById('File', file_id)
            print("Entering versioning for: ", file['name'])

            directory = getEntityById('Directory', file['root'])
            current_directory = directory['name']

            versions = getBlobVersions(file)

            version_count = len(list(versions))

            version_list = file['versions']

            print("versions found: ", version_count)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('versions.html', user_data=claims, error_message=error_message, file=file, current_directory=current_directory, version_count=version_count, version_list=version_list)


@app.route('/enter_directory/<dirname>', methods=['POST'])
def enterDirectoryHandler(dirname):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    files = []
    directory = None

    memory = 0

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            directory = getEntityById("Directory", dirname)

            files = retrieveFileEntities(directory)

            collectMemory(user_info)

            dir_mem = directory['size']

            memory = user_info['size']

        except ValueError as exc:
            error_message = str(exc)

    return render_template('directory.html', user_data=claims, error_message=error_message,
                           user_info=user_info,
                           files=files, directory=directory, memory=memory)


@app.route('/add_directory', methods=['POST'])
def addDirectoryHandler():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            directory_name = request.form['dir_name']
            if directory_name == '' or directory_name.find('/') != -1:
                return redirect('/')

            user_info = retrieveUserInfo(claims)
            addDirectoryBlob(claims['user_id'] + '/' + directory_name+'/')
            # adding directory to datastore
            id = createDirectoryEntity(claims['user_id'], directory_name)
            addDirectoryToUser(user_info, id)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/upload_file_share', methods=['POST'])
def uploadFileFromShareHandler():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    shared = None
    owned_list = []
    collab_list = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)

            user_info = retrieveUserInfo(claims)

            file = request.files['file_name']

            file_owner = request.form['owner']
            shared_key = request.form['dir_key']
            file_key = request.form['file_key']

            uploadFromShared(file_owner, file_key, file)

            owned_list, collab_list = getSharedFiles(user_info)
            shared = getEntityById('Directory', shared_key)

            collectMemory(user_info)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('share.html', user_data=claims, error_message=error_message, owned_list=owned_list, collab_list=collab_list, shared=shared)


@app.route('/upload_file_dir/<key>', methods=['POST'])
def uploadFileFromDirectoryHandler(key):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    directory = None
    file_size = 0
    files = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            file = request.files['file_name']

            if file.filename == '':
                return redirect('/')
            user_info = retrieveUserInfo(claims)

            directory = getEntityById("Directory", key)

            file_size = uploadFromDirectory(user_info, file, directory, key)

            # Update memory usage in directory
            updateMemory(directory, file_size)
            print('updating memory, increasing by ', file_size)

            files = retrieveFileEntities(directory)

            collectMemory(user_info)

        except ValueError as exc:
            error_message = str(exc)
    return render_template('directory.html', user_data=claims, error_message=error_message,
                           user_info=user_info,
                           files=files, directory=directory)


@app.route('/upload_file/<key>', methods=['POST'])
def uploadFileHandler(key):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    directory = None
    file_size = 0

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            file = request.files['file_name']
            if file.filename == '':
                return redirect('/')
            user_info = retrieveUserInfo(claims)

            directory = getEntityById("Directory", key)

            file_size = uploadFromDirectory(user_info, file, directory, key)

            # Update memory usage in directory
            updateMemory(directory, file_size)
            print('updating memory, increasing by ', file_size)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/delete_file/<filekey>', methods=['POST'])
def deleteFileHandle(filekey):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    file_bytes = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            deleteFile(user_info, filekey)

        except ValueError as exc:
            error_message = str(exc)

    return redirect('/')


@app.route('/delete_directory/<string:dirname>', methods=['POST'])
def deleteDirectoryHandler(dirname):
    id_token = request.cookies.get("token")
    claims = None
    user_info = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            deleteDirectory(user_info, dirname)

        except ValueError as exc:
            error_message = str(exc)

    return redirect('/')


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    file_list = []
    directories = []
    root = None
    files = []
    root_id = None
    memory = 0
    sharing_id = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            user_info_id = claims['user_id']

            # Check if versioning is enabled and if not enables it
            print(enable_versioning())

            # Upon first login initialise entities
            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
                id = createDirectoryEntity(user_info_id, claims['user_id'])
                addDirectoryToUser(user_info, id)
                addDirectoryBlob(user_info_id+"/"+"versions/")

                user_info.update({
                    'root_key': id
                })
                datastore_client.put(user_info)

                sharing_id = createDirectoryEntity(user_info_id, 'shared')
                addDirectoryToUser(user_info, sharing_id)
                print('created sharing: ', sharing_id)

            sharing = retrieveDirectoryEntity(user_info, 'shared')
            sharing_id = sharing['key']
            print('retrieved sharing: ', sharing_id)

            # Fetch viewable directory list from datastore
            directories = getViewingDirectories(user_info)

            root = retrieveDirectoryEntity(user_info, user_info_id)
            print("root: ", root)
            files = retrieveFileEntities(root)
            print('Files: ', files)
            root_id = root['key']

            collectMemory(user_info)

            memory = user_info['size']

        except ValueError as exc:
            error_message = str(exc)

    return render_template('main.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list_size=len(
                               files),
                           files=files, directories=directories, dir_key=root_id, memory=memory)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
