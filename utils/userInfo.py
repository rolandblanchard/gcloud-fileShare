import datetime
import random
import local_constants
import google.oauth2.id_token
from google.auth.transport import requests
from google.cloud import datastore, storage
from flask import Flask, render_template, request, redirect, Response

from utils.helper import getEntityById

datastore_client = datastore.Client()


def createUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore.Entity(key=entity_key)
    entity.update({
        'user_id': claims['user_id'],
        'email': claims['email'],
        'name': claims['name'],
        'directory_list': [],
        'root_key': "",
        'size': 0
    })
    datastore_client.put(entity)


def retrieveUserInfo(claims):
    entity_key = datastore_client.key('UserInfo', claims['email'])
    entity = datastore_client.get(entity_key)
    return entity


def getDirectoryList(claims, dirname):

    entity = retrieveUserInfo(claims)
    dirs = entity['directory_list']

    if (dirname != ""):
        dirs.remove(dirname)
        return dirs

    return dirs


def getAllUsers():

    query = datastore_client.query(kind='UserInfo')

    # Retrieve the results from the query
    results = list(query.fetch())

    # Print the email property of each UserInfo entity
    for result in results:
        print(result['email'])

    return results


def getUserInfoByEmail(email):

    query = datastore_client.query(kind='UserInfo')
    query.add_filter('email', '=', email)

    results = list(query.fetch(1))

    if not results:
        return None

    return results[0]
