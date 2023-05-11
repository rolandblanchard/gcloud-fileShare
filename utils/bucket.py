from google.cloud import storage
import datetime
import random
import local_constants
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

datastore_client = datastore.Client()


''' Returns all blobs in any directory '''
# Unused


def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)


''' Uploads directory blob to directory, default is uuid '''


def addDirectoryBlob(directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name)
    blob.upload_from_string(
        '', content_type='application/x-www-form-urlencoded;charset=UTF-8')


''' Uploads file blob to directory, default is uuid '''


def addFileBlob(file, directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name + file.filename)
    blob.upload_from_file(file)

    return blob


''' Downloads a blob '''
# Unused


def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(filename)
    return blob.download_as_bytes()


''' Deletes a file blob '''


def deleteFileBlob(file):

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file['path']+file['name'])
    blob.delete()

    return blob


''' Deletes a directory blob '''


def deleteDirectoryBlob(directory_name):
    file = None
    if directory_name == 'root':
        return False

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name+'/')

    blob.delete()

    return True


''' Function to get a blob file without versions '''
# Unused


def getBlob(file):

    if file == None:
        print("failed to getBlob file: ", file)
        return None
    file_path = file['path']+file['name']

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(file_path)

    if blob.exists():
        return blob
    else:
        print("failed to getBlob from: ", file['name'], file['key'])
        return None


''' Moves any blob to a new versions folder'''
# Unused


def moveFileToVersion(old_file):

    source_path = old_file['path']
    file_name = old_file['name']
    source_blob_name = source_path + file_name
    destination_blob_name = old_file['user_id']+"/versions/"+file_name
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


''' Function to pull a full version list of a blob given the file entity '''


def getBlobVersions(file):

    if file == None:
        print("failed to getBlob file: ", file)
        return None

    file_path = file['path']+file['name']

    # Create a client object
    storage_client = storage.Client()

    # Get the bucket object
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # Get all versions of the file
    all_versions = bucket.list_blobs(
        versions=True,
        prefix=file_path
    )

    return all_versions


''' Funtion to extract the latest blob version given the file entity'''


def getPreviousVersion(file, latest_generation):

    versions = getBlobVersions(file)
    previous_version = None
    for i in versions:
        if i.generation == latest_generation:
            print('found latest')
            return previous_version
        else:
            previous_version = i

    return None


def enable_versioning():

    # Initialize a client object
    storage_client = storage.Client()

    # Retrieve the bucket object
    bucket = storage_client.get_bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # Check if versioning is already enabled
    if bucket.versioning_enabled:
        print(
            f"Versioning is already enabled for bucket {local_constants.PROJECT_STORAGE_BUCKET}")
    else:
        # Enable versioning for the bucket
        bucket.versioning_enabled = True
        bucket.patch()
        print(
            f"Versioning has been enabled for bucket {local_constants.PROJECT_STORAGE_BUCKET}")


def deleteBlobVersion(blob_name, generation):

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(blob_name, generation=generation)
    blob_size = blob.size

    if blob.delete() == None:
        return blob_size


def downloadBlobVersion(blob_name, generation):

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(blob_name, generation=generation)

    return blob.download_as_bytes()


def getUserMemoryUsage(user_id):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.get_bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.get_blob(user_id)
    print("memory blob ", blob, user_id)

    return blob.size
