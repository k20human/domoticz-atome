#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Copyright (C) 2017 Kévin Mathieu
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.
#

import requests


class URL:
    def __init__(self, url):
        self.baseUrl = 'http://' + url + '/json.htm'

    def call(self, params = None):
        req = requests.get(self.baseUrl, params=params)

        return req
