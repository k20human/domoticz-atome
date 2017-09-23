#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""

@author: k20human

"""

#
# Copyright (C) 2017 Kévin Mathieu
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.
#

import atome
import json
import os
import sys
import logging
import url
import datetime
from logging.handlers import RotatingFileHandler

# Configuration file path
configurationFile = './config.json'

# Configure logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

file_handler = RotatingFileHandler('atome.log', 'a', 1000000, 1)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.INFO)
steam_handler.setFormatter(formatter)
logger.addHandler(steam_handler)

# Check if configuration file exists
if os.path.isfile(configurationFile):
    # Import configuration file
    with open(configurationFile) as data_file:
        config = json.load(data_file)
else:
    logger.error('Your configuration file doesn\'t exists')
    sys.exit('Your configuration file doesn\'t exists')

# Domoticz server & port information
domoticzServer = config['domoticz_server']

# Domoticz IDX
domoticzIdx = config['domoticz_idx']

# Atome Login
atomeLogin = config['atome_login']

# Atome password
atomePassword = config['atome_password']

# Atome user ID
atomeUserId = config['atome_user_id']

# Domoticz API
domoticzApi = url.URL(domoticzServer)


def get_counter_value():
    # Get value from Domoticz
    counter = domoticzApi.call({
        'type': 'devices',
        'rid': domoticzIdx
    }).json()

    # T1: creuse, T2: pleine
    counterValues = counter['result'][0]['Data'].split(";")

    return {
        'creuse': int(counterValues[0]),
        'pleine': int(counterValues[1]),
    }


def get_current_index():
    now = datetime.datetime.now()

    today0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today630 = now.replace(hour=6, minute=30, second=0, microsecond=0)
    today2230 = now.replace(hour=22, minute=30, second=0, microsecond=0)
    today2359 = now.replace(hour=23, minute=59, second=0, microsecond=0)

    if now >= today0 and now < today630:
        return 'creuse'
    elif today630 >= today0 and now < today2230:
        return 'pleine'
    elif today2230 >= today0 and now <= today2359:
        return 'creuse'


def login():
    try:
        # Login
        logger.info("Logging as %s", atomeLogin)

        return atome.login(atomeLogin, atomePassword)
    except atome.LoginException as exc:
        logger.error(exc)
        sys.exit(1)


def get_data(token, prevent_while):
    try:
        # Get data
        logger.info("Get dats from Atome")

        return atome.get_data(token, atomeUserId)
    except atome.LoginException as exc:
        if prevent_while < 2:
            # Cookie as expired
            token = login()
            return get_data(token, prevent_while + 1)
        else:
            logger.error(exc)
            sys.exit(1)
    except atome.AtomeException as exc:
        logger.error(exc)
        sys.exit(1)


# Main script
def main():
    token = login()

    values = get_data(token, 0)
    counter = get_counter_value()
    current_index = get_current_index()

    # Get last value period (ie: if it's 22h29 get 22h00 - 22h30 period)
    true_values = values['results'][0]['series'][0]['values']
    last_value = true_values[-1]

    # Create new counter value
    counter[current_index] += last_value[1]

    # Update Domoticz
    res = domoticzApi.call({
        'type': 'command',
        'param': 'udevice',
        'idx': domoticzIdx,
        'svalue': str(counter['creuse']) + ';' + str(counter['pleine']) + ';0;0;0;0'
    })

    if res.status_code == 200:
        logger.info('Data successfully send to Domoticz')
    else:
        logger.error('Can\'t send data to Domoticz')

if __name__ == "__main__":
    main()
