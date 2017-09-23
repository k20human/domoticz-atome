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
API_ENDPOINT_LOGIN = '/login'
API_ENDPOINT_LOGIN_CHECK = '/login_check'
API_ENDPOINT_DATA = '/api/graph/api/datasources/proxy/3/query'

COOKIE_FILE = './cookie'
COOKIE_NAME = 'PHPSESSID'

class AtomeException(Exception):
    pass

class LoginException(Exception):
    # Thrown if an error was encountered while retrieving energy consumption data.
    pass

def save_cookie(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookie(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def get_cookie():
    cookie = load_cookie(COOKIE_FILE)

    return cookie

def get_csrf_token():
    req = requests.get(API_BASE_URI + API_ENDPOINT_LOGIN)
    soup = BeautifulSoup(req.content, "html.parser")

    return {
        'csrf_token': soup.find("input", {"name": "_csrf_token"})['value'],
        'cookie': req.cookies.get(COOKIE_NAME)
    }

def login(username, password):
    # Try to load cookie from file
    if os.path.isfile(COOKIE_FILE):
        return get_cookie()

    # Get CSRF token
    token = get_csrf_token()
    cookie = {COOKIE_NAME: token['cookie']}

    # Login the user into the Linky API.
    payload = {'_username': username,
               '_password': password,
               '_csrf_token': token['csrf_token'],
               '_remember_me': 'on',
               '_submit': 'Connexion'}

    req = requests.post(API_BASE_URI + API_ENDPOINT_LOGIN_CHECK, data=payload, cookies=cookie, allow_redirects=False)
    session_cookie = req.cookies.get(COOKIE_NAME)

    if session_cookie is None:
        raise LoginException("Login unsuccessful. Check your credentials")

    # Store cookie inside file
    save_cookie(session_cookie, COOKIE_FILE)

    return get_cookie()

def get_data(token, user_id):
    # We send the session token so that the server knows who we are
    cookie = {COOKIE_NAME: token}

    params = {
        'db': 'esoftlink',
        'epoch': 's',
        'q': (
            'SELECT max("energyActiveConsumedTotal") - min("energyActiveConsumedTotal")'
            ' FROM "electrical"'
            ' WHERE "user_id" =~ /^' + user_id + '$/  AND time > now() - 24h and time < now() - 1s'
            ' GROUP BY time(30m) fill(null)'
        )
    }

    req = requests.get(API_BASE_URI + API_ENDPOINT_DATA, allow_redirects=False, cookies=cookie, params=params)

    if req.status_code == 302:
        os.remove(COOKIE_FILE)
        raise LoginException("Cookie expired")

    if req.status_code != 200:
        raise AtomeException('Can\'t get data from Atome')

    return req.json()
