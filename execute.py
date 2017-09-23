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
import datetime
import url
import time
from dateutil.relativedelta import relativedelta
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
    print(counterValues)

# Export data to Domoticz
def export_days_values(res):
    value = res['graphe']['data'][-1]['valeur']

    if value < 0:
        raise linky.LinkyLoginException('Value is less than 0, error in API')

    # Send to Domoticz only if data not send today
    if lastUpdate != time.strftime("%Y-%m-%d"):
        res = domoticzApi.call({
            'type': 'command',
            'param': 'udevice',
            'idx': domoticzIdx,
            'svalue': counterValue + int(value * 1000)
        })

        if res.status_code == 200:
            logger.info('Data successfully send to Domoticz')
        else:
            raise linky.LinkyLoginException('Can\'t add data to Domoticz')
    else:
        logger.info('Data already successfully send to Domoticz today')

# Date formatting
def dtostr(date):
    return date.strftime("%d/%m/%Y")

def get_data_per_day(token):
    today = datetime.date.today()

    return linky.get_data_per_day(token, dtostr(today - relativedelta(days=1, months=1)),
                                     dtostr(today - relativedelta(days=1)))

# Main script
def main():
    try:
        logger.info("Logging as %s", atomeLogin)

        get_counter_value()

        # Login
        token = atome.login(atomeLogin, atomePassword)

        # Get data
        atome.get_data(token, atomeUserId)

        # Get datas
        # res_day = call_enedis_api()
        #
        # logger.info("Logged in successfully!")
        # logger.info("Retreiving data...")
        #
        # logger.info("Got datas!")
        #
        # # Send to Domoticz
        # export_days_values(res_day)

    except atome.LoginException as exc:
        logger.error(exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
