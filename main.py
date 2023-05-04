import datetime
import random
import local_constants
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.userInfo import *
from utils.directory import *
from utils.file import *
from utils.bucket import *


app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


@app.route('/delete_file/<string:file_name>', methods=['POST'])
def deleteFileFromDirectory(file_name):
    id_token = request.cookies.get("token")
    error_message = None
    directory = None

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            deleteFileEntity(directory, file_name)
        except ValueError as exc:
            error_message = str(exc)

    return redirect('/')


@app.route('/enter_directory/<dirname>/', methods=['POST'])
def enterDirectoryHandler(dirname):
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    file_list = []
    directory_list = []

    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter)
            user_info = retrieveUserInfo(claims)

            blob_list = blobList(dirname)
            for i in blob_list:
                if i.name[len(i.name) - 1] == '/':
                    directory_list.append(i)
                else:
                    file_list.append(i)

        except ValueError as exc:
            error_message = str(exc)

    return render_template('directory.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list=file_list, directory_list=directory_list, directory_name=dirname)


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
            if directory_name == '' or directory_name[len(directory_name) - 1] != '/':
                return redirect('/')
            user_info = retrieveUserInfo(claims)
            addDirectory(directory_name)
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
            print("test-> ", directory)
            filename = str(file.filename)
            directory_name = "" if dirname == "root" else dirname+"/"
            addFile(file, directory_name)
            createFileEntity(filename, dirname)
            addFileToDirectory(directory, filename)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/handle_file/<string:filename>', methods=['POST'])
def downloadFile(filename):
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
        except ValueError as exc:
            error_message = str(exc)
    print("Request-> ", request)

    # return Response(downloadBlob(filename), mimetype='application/octet-stream')


@app.route('/')
def root():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    file_list = []
    directory_list = []
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            user_info = retrieveUserInfo(claims)
            if user_info == None:
                createUserInfo(claims)
                user_info = retrieveUserInfo(claims)
                createDirectoryEntity("root")
                addDirectoryToUser(user_info, "root")
            blob_list = blobList(None)
            for i in blob_list:
                if i.name[len(i.name) - 1] == '/':
                    directory_list.append(i)
                else:
                    file_list.append(i)
        except ValueError as exc:
            error_message = str(exc)
    return render_template('main.html', user_data=claims, error_message=error_message,
                           user_info=user_info, file_list=file_list, directory_list=directory_list)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
