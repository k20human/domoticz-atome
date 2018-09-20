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
import base64
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

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

# Domoticz user
domoticzLogin = config['domoticz_login']

# Domoticz password
domoticzPassword = config['domoticz_password']

# Atome Login
atomeLogin = config['atome_login']

# Atome password
atomePassword = config['atome_password']

# Domoticz API
if domoticzLogin:
    b64domoticzlogin = base64.b64encode(domoticzLogin.encode())
    b64domoticzpassword = base64.b64encode(domoticzPassword.encode())
    domoticzServer = domoticzServer + '/json.htm?username=' + b64domoticzlogin.decode() + '&password=' + b64domoticzpassword.decode()
else:
    domoticzServer = domoticzServer + '/json.htm'

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
    now = datetime.now()

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


def get_data(token, user_ids, prevent_while):
    try:
        # Get data
        logger.info("Get dats from Atome")

        return atome.get_data(token, user_ids)
    except atome.LoginException as exc:
        if prevent_while < 2:
            # Cookie as expired
            token, user_ids = login()
            return get_data(token, user_ids, prevent_while + 1)
        else:
            logger.error(exc)
            sys.exit(1)
    except atome.AtomeException as exc:
        logger.error(exc)
        sys.exit(1)


# Main script
def main():
    token, user_ids = login()

    values = get_data(token, user_ids, 0)
    counter = get_counter_value()
    current_index = get_current_index()

    last_value = {
        'creuse': 0,
        'pleine': 0,
    }
    now = datetime.now()

    # Get last value period (ie: if it's 22h29 get 22h00 - 22h30 period)
    for value in values['data']:
        time = datetime.strptime(value['time'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=2)
        if time.date() == now.date() and time.hour == now.hour:
            last_value['creuse'] = value['consumption']['index1']
            last_value['pleine'] = value['consumption']['index2']

    # Log infos
    logger.info("Current index: %s", current_index)
    logger.info("Counter HC: %d", counter['creuse'])
    logger.info("Counter HP: %d", counter['pleine'])
    logger.info("Current kwh HC: %d", last_value['creuse'])
    logger.info("Current kwh HP: %d", last_value['pleine'])

    # Create new counter value
    counter[current_index] += last_value[current_index]

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
