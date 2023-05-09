from google.cloud import storage
import datetime
import random
import local_constants
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

datastore_client = datastore.Client()


def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)


def addDirectory(directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name)
    blob.upload_from_string(
        '', content_type='application/x-www-form-urlencoded;charset=UTF-8')


def addFile(file, directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name + file.filename)
    blob.upload_from_file(file)


def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    return blob.download_as_bytes()


def deleteFileBlob(file):

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file['path']+file['name'])

    return blob.delete()


def deleteDirectoryBlob(directory_name):
    file = None
    if directory_name == 'root':
        return False

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name+'/')

    blob.delete()

    return True


def getBlob(directory_name, file_name):

    file = None
    if directory_name == 'root':
        file = file_name
    else:
        file = directory_name + file

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file)

    if blob.exists():
        return blob
    else:
        return None


def addVersion(directory_name, file):

    return True


def moveFileToVersion(source_path, file_name):
    """Move a file within the same bucket."""
    source_blob_name = source_path + file_name
    destination_blob_name = "versions/"+file_name
    # Initialize a client
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    # Get the source and destination blobs
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    source_blob = bucket.blob(source_blob_name)

    # Copy the source blob to the destination blob
    bucket.copy_blob(source_blob, bucket, destination_blob_name)
    # Delete the source blob
    source_blob.delete()

    print(
        f"Moved {source_blob_name} to {destination_blob_name} in the bucket")
