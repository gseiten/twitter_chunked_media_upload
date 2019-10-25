
from main.commons.oauth1 import build_params, make_oauth
from tornado.gen import coroutine
import mimetypes
import os
import json
import requests
from pprint import pprint
from urllib.parse import urlencode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from os.path import abspath, realpath
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
PATH = '../images/{}'
from main.commons import async_upload

http_client = AsyncHTTPClient()

cred = {
    "oauth_token": "",
    "oauth_token_secret": "",
}


@coroutine
def init(file_name):

    url = "https://upload.twitter.com/1.1/media/upload.json"
    mform_data = {
        "command": "INIT",
        "total_bytes": str(os.path.getsize(PATH.format(file_name))),
        "media_type": mimetypes.guess_type(PATH.format(file_name))[0] or "application/octet-stream"}
    auth_params = build_params(extras={
        "oauth_token": cred["oauth_token"],
        "oauth_token_secret": cred["oauth_token_secret"]})
    headers = make_oauth(url, "post", auth_params, args=mform_data)

    url = "https://upload.twitter.com/1.1/media/upload.json?command=INIT&total_bytes={}&media_type={}".format(
        str(os.path.getsize(PATH.format(file_name))),
        mimetypes.guess_type(PATH.format(file_name))[0])

    try:
        response = yield http_client.fetch(url, method='POST', headers=headers, allow_nonstandard_methods=True)
        media_details = json.loads(response.body.decode())
        return media_details['media_id_string']
    except HTTPError as err:
        print("ERROR: ", str(err))


@coroutine
def append(file_name, media_id):

    segment = 0
    url = "https://upload.twitter.com/1.1/media/upload.json"
    auth_params = build_params(extras={
        "oauth_token": cred["oauth_token"],
        "oauth_token_secret": cred["oauth_token_secret"]
    })
    headers = make_oauth(url, "post", auth_params, args=None)

    with open(PATH.format(file_name), 'rb') as f:
        while True:
            chunk = f.read(1 * 500000)
            if not chunk:
                break

            mform_data = {
                "media": chunk,
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": str(segment)}
            segment += 1

            print(segment)

            request = requests.Request(url=url, files=mform_data, data=dict())
            prepared = request.prepare()
            body = prepared.body
            headers.update({
                "Content-Type": prepared.headers.get('Content-Type')
            })

            twitter_upload = HTTPRequest(url=url, headers=headers, method='POST', body=body)
            try:
                response = yield http_client.fetch(twitter_upload)
                print("UPLOAD: ", response.body)
            except HTTPError as err:
                print("Error: ", str(err))

    return


@coroutine
def finalize(media_id):

    url = "https://upload.twitter.com/1.1/media/upload.json"
    mform_data = {
        "command": "FINALIZE",
        "media_id": media_id}

    auth_params = build_params(extras={
        "oauth_token": cred["oauth_token"],
        "oauth_token_secret": cred["oauth_token_secret"]})

    headers = make_oauth(url, "post", auth_params, args=mform_data)
    url += "?" + urlencode(mform_data)

    try:
        response = yield http_client.fetch(url, method='POST', headers=headers, allow_nonstandard_methods=True)
        return json.loads(response.body.decode())
    except HTTPError as err:
        print("ERROR: ", str(err))


@coroutine
def status(media_id):

    url = "https://upload.twitter.com/1.1/media/upload.json"
    q_args = {
        "command": "STATUS",
        "media_id": str(media_id)}

    auth_params = build_params(extras={
        "oauth_token": cred["oauth_token"],
        "oauth_token_secret": cred["oauth_token_secret"]})

    headers = make_oauth(url, "get", auth_params, args=q_args)
    url += "?" + urlencode(q_args)

    try:
        response = yield http_client.fetch(url, method='GET', headers=headers)
        return json.loads(response.body.decode())
    except HTTPError as err:
        print("ERROR: ", str(err))


@coroutine
def media_tweet(media_id):

    url = "https://api.twitter.com/1.1/statuses/update.json"
    auth_params = build_params(extras={
        "oauth_token": cred["oauth_token"],
        "oauth_token_secret": cred["oauth_token_secret"]})
    q_args = {
        "status": "chunk upload video",
        "media_ids": media_id
    }
    headers = make_oauth(url, "post", auth_params, args=q_args)
    url += '?' + urlencode(q_args)
    try:
        response = yield http_client.fetch(url, method='POST', headers=headers, allow_nonstandard_methods=True)
        return json.loads(response.body.decode())
    except HTTPError as err:
        print("Error: ", str(err))


@coroutine
def chunked_upload(file_name=None):

    file_name = "fbtest3.mp4"
    media_id = yield init(file_name)
    segment_status = yield append(file_name, media_id)
    upload_details = yield finalize(media_id)
    tweet = yield media_tweet(media_id)
    pprint(tweet)
