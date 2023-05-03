import datetime
import random
import local_constants
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response
app = Flask(__name__)
datastore_client = datastore.Client()

firebase_request_adapter = requests.Request()


def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'email': claims['email'],
        'name': claims['name'],
        'directory_list': []
    })
    datastore_client.put(entity)


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity

# doesn't avoid dups!!


def createDirectoryEntity(claims, directory_name):
    id = random.getrandbits(63)

    entity_key = datastore_client.key('Directory', id)
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'name': directory_name,
        'subDirectories': []
    })

    datastore_client.put(entity)

    return id


def addDirectoryToUser(user_info, id):
    directory_keys = user_info['directory_list']
    directory_keys.append(id)
    user_info.update({
        'directory_list': directory_keys
    })
    datastore_client.put(user_info)


def deleteDirectoryEntity(claims, id):
    user_info = retrieveUserInfo(claims)
    directory_list_keys = user_info['directory_list']

    directory_key = datastore_client.key('Directory', directory_list_keys[id])
    datastore_client.delete(directory_key)

    del directory_list_keys[id]
    user_info.update({
        'directory_list': directory_list_keys
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


def createFileEntity(claims):
    return None


def retrieveFileEntity(claims):
    return None


def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)


def addDirectory(directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name)
    blob.upload_from_string(
        '', content_type='application/x-www-form-urlencoded;charset=UTF-8')


def addFile(file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)


def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    return blob.download_as_bytes()


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
            id = createDirectoryEntity(claims, directory_name)
            addDirectoryToUser(user_info, id)

        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/upload_file', methods=['post'])
def uploadFileHandler():
    id_token = request.cookies.get("token")
    error_message = None
    claims = None
    times = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
                                                                  firebase_request_adapter)
            file = request.files['file_name']
            if file.filename == '':
                return redirect('/')
            user_info = retrieveUserInfo(claims)
            addFile(file)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')


@app.route('/download_file/<string:filename>', methods=['POST'])
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
    return Response(downloadBlob(filename), mimetype='application/octet-stream')


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
