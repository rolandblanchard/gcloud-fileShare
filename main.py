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


app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


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

            # Fetch file list from datastore
            file_list = getFileList(dirname)
            print("file_list: ", file_list)
            directory = retrieveDirectoryEntity(dirname)
            files = retrieveFileEntities(directory)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('directory.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list=file_list, file_list_size=len(
                               file_list),
                           files=files, current_directory=dirname)


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
            addDirectory(directory_name+'/')
            # adding directory to datastore
            id = createDirectoryEntity(directory_name)
            addDirectoryToUser(user_info, id)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/upload_file/<string:dirname>', methods=['POST'])
def uploadFileHandler(dirname):
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

            directory = retrieveDirectoryEntity(dirname)

            filename = str(file.filename)
            directory_name = "" if dirname == "root" else dirname+"/"
            addFile(file, directory_name)
            createFileEntity(filename, dirname)
            addFileToDirectory(directory, filename)

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

            deleteFile(filename)

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
    directory_list = []
    root = None
    files = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            # Upon first login initialise entities
            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
                createDirectoryEntity("root")
                addDirectoryToUser(user_info, "root")

            # Fetch file list from datastore
            file_list = getFileList("root")

            # Fetch directory list from datastore
            directory_list = getDirectoryList(claims, "root")
            root = retrieveDirectoryEntity("root")
            files = retrieveFileEntities(root)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('main.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list=file_list, file_list_size=len(
                               file_list),
                           files=files, directory_list=directory_list, current_directory="root")


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
