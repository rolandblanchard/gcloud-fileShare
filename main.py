import datetime
import random
import local_constants
import urllib.parse
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response, url_for

from utils.userInfo import *
from utils.directory import *
from utils.file import *
from utils.bucket import *
from utils.versions import *


app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


def getEntityById(type, id):
    key = datastore_client.key(type, id)
    return datastore_client.get(key)


@app.route('/versions/<string:file_name>', methods=['POST'])
def deleteFileFromDirectory(file_name):
    id_token = request.cookies.get("token")
    error_message = None
    directory = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
        except ValueError as exc:
            error_message = str(exc)

    return render_template('versions.html')


@app.route('/enter_directory/<dirname>', methods=['POST'])
def enterDirectoryHandler(dirname):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    user_info = None
    file_list = []
    directory_list = []
    files = []
    directory = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            directory = getEntityById("Directory", dirname)

            files = retrieveFileEntities(directory)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('directory.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list_size=len(
                               files),
                           files=files, current_directory=directory['name'], dir_key=directory['key'])


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
            addDirectory(claims['user_id'] + '/' + directory_name+'/')
            # adding directory to datastore
            id = createDirectoryEntity(claims['user_id'], directory_name)
            addDirectoryToUser(user_info, id)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/upload_file/<key>', methods=['POST'])
def uploadFileHandler(key):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    directory = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            file = request.files['file_name']
            if file.filename == '':
                return redirect('/')
            user_info = retrieveUserInfo(claims)

            directory = getEntityById("Directory", key)

            filename = str(file.filename)

            directory_name = claims['user_id'] + '/'
            print("oops: ", key, '|', user_info['root_key'])
            if key != user_info['root_key']:
                print("oops: ", key, '|', user_info['root_key'])
                directory_name = directory_name + directory['name']+'/'

            print("dirname: ", directory_name)

            # if checkIfVersion(directory['file_list'], filename):
            #     # get old file
            #     old_file = getFileEntity(filename)
            #     # create version from old_file
            #     new_version = createVersionEntity(old_file)
            #     addVersionToFile(old_file, new_version)
            #     moveFileToVersion(directory_name, filename)

            # else:

            id = createFileEntity(claims['user_id'], filename, directory_name)

            addFileToDirectory(directory, id)

            addFile(file, directory_name)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/delete_file/<string:filename>', methods=['POST'])
def deleteFileHandle(filename):
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
            deleteFile(user_info, filename)

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

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            user_info_id = claims['user_id']

            # Upon first login initialise entities
            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
                id = createDirectoryEntity(user_info_id, claims['user_id'])
                addDirectoryToUser(user_info, id)
                addDirectory(user_info_id+"/"+"versions/")

                user_info.update({
                    'root_key': id
                })
                datastore_client.put(user_info)

            # Fetch directory list from datastore
            directories = retrieveDirectories(user_info)

            root = retrieveDirectoryEntity(user_info, user_info_id)
            print("root: ", root)
            files = retrieveFileEntities(root)
            print('Files: ', files)
            root_id = root['key']

        except ValueError as exc:
            error_message = str(exc)

    return render_template('main.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list_size=len(
                               files),
                           files=files, directories=directories, dir_key=root_id)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
