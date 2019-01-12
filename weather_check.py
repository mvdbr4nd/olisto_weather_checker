#!/usr/bin/python3

import requests
import os
import sys
import json
import time
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

def check_weather(data):

    # get the max sunpower for the station above
    # zonintensiteitWM2

    page = requests.get(data['api_url'])
    if page.status_code == 200:
        res = json.loads(page.text)
        max_sunpower = float(0)
        for ws in res['actual']['stationmeasurements']:
            if ws['regio'] in data['regions']:
                try:
                    sunpower = float(ws['sunpower'])
                    if (sunpower > max_sunpower):
                        max_sunpower = sunpower
                except BaseException:
                    logger.error("Error parsing reponse from KNMI")

        if check_weather.last_sunpower != max_sunpower:
            logger.debug("Got new sunpower %s"%(max_sunpower))
            check_weather.last_sunpower = max_sunpower
            url = '%s?value=%s'%(data['olisto_connector'], max_sunpower)
            requests.post(url)
    else:
        logger.error("failed to get weather data")

check_weather.last_sunpower = 0

if __name__ == '__main__':
    handler = RotatingFileHandler(
        'weather_check.log',
        maxBytes=100000,
        backupCount=30)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)-22s - %(levelname)-8s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    handler_stdout = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler_stdout)
    logger.setLevel(logging.DEBUG)
    logger.info("Starting Olisto Weather checker")

    try:
        with open('weather_check.json') as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        logger.error("Failed to open configuration, create the configuration file: weather_check.json")
        sys.exit()
    except ValueError:
        logger.error("Failed to parse configuration")
        sys.exit()

    while True:
        check_weather(data)
        time.sleep(data['interval'])
