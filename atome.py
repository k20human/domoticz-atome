#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Get Linky informations from Atome device
"""

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from bs4 import BeautifulSoup
import requests
import pickle
import os
import sys

API_BASE_URI = 'https://esoftlink.esoftthings.com'
API_ENDPOINT_LOGIN = '/api/user/login.json'
API_ENDPOINT_DATA = '/graph-query-last-consumption'

USER_FILE = './user'
COOKIE_FILE = './cookie'
COOKIE_NAME = 'PHPSESSID'

class AtomeException(Exception):
    pass

class LoginException(Exception):
    # Thrown if an error was encountered while retrieving energy consumption data.
    pass

def save_file(request, filename):
    with open(filename, 'wb') as f:
        pickle.dump(request, f)

def load_file(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def get_cookie():
    cookie = load_file(COOKIE_FILE)

    return cookie

def get_user():
    user = load_file(USER_FILE)

    return user

def login(username, password):
    # Try to load cookie from file
    if os.path.isfile(COOKIE_FILE) and os.path.isfile(USER_FILE):
        return get_cookie(), get_user()

    # Login the user into the Atome API.
    payload = {"email": username,
               "plainPassword": password}

    req = requests.post(API_BASE_URI + API_ENDPOINT_LOGIN, json=payload, headers={"content-type":"application/json"})
    response_json = req.json()
    session_cookie = req.cookies.get(COOKIE_NAME)

    if session_cookie is None:
        raise LoginException("Login unsuccessful. Check your credentials")

    # Store cookie inside file
    save_file(session_cookie, COOKIE_FILE)

    # Store user inside file
    save_file(str(response_json['id']) + '_' + response_json['subscriptions'][0]['reference'], USER_FILE)

    return get_cookie(), get_user()

def get_data(token, user_ids):
    # We send the session token so that the server knows who we are
    cookie = {COOKIE_NAME: token}
    user_id, user_reference = user_ids.split('_')

    params = {
        'period': 'day',
        'objective': 'false'
    }

    url = API_BASE_URI + '/' + user_id + '/' + user_reference + API_ENDPOINT_DATA
    req = requests.get(url, cookies=cookie, params=params)

    if req.status_code == 302:
        os.remove(COOKIE_FILE)
        raise LoginException("Cookie expired")

    if req.status_code != 200:
        raise AtomeException('Can\'t get data from Atome')

    return req.json()
