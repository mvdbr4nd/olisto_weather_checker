#!/usr/bin/python3

import requests
import os
import sys
import json
import time
import logging
import datetime
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

def check_weather(data):
    logger.debug("checking weather")
    try:
        page = requests.get(data['api_url'])
        if page.status_code == 200:
            res = json.loads(page.text)
            sum_sunpower = float(0)
            max_windstoten = float(0)
            max_wind = float(0)
            sum_temp = float(0)
            sum_humidity = float(0)
            logger.debug("find weather stations")
            for ws in res['actual']['stationmeasurements']:
                if ws['regio'] in data['regions']:
                    try:
                        sum_sunpower += float(ws['sunpower'])
                        
                        wind = float(ws['windspeed'])
                        if (wind > max_wind):
                            max_wind = wind

                        windstoten = float(ws['windgusts'])
                        if windstoten > max_windstoten:
                            max_windstoten = windstoten					

                        sum_temp += float(ws['temperature'])
                        sum_humidity += float(ws['humidity'])
       
                    except BaseException:
                        logger.error("Error parsing reponse from KNMI")


            if data['pilight_enabled']:
                avg_temp = round(float(sum_temp / float(len(data['regions']))),2)
                avg_sunpower = round(float(sum_sunpower / float(len(data['regions']))),2)
                #avg_humidity = round(float(sum_humidity / float(len(data['regions']))),2)
                try:
                    os.system("pilight-send -p generic_label -i %s -l '%s MW2'"%(data['pilight_label'], avg_sunpower))
                    logger.debug("update sun power")
                    os.system("pilight-send -p generic_label -i %s -l '%s MS, %s MS'"%(data['pilight_wind_label'], max_wind, max_windstoten))
                    logger.debug("update wind")
                    os.system("pilight-send -p generic_label -i %s -l '%s Celsius'"%(data['pilight_temp_label'], avg_temp))
                    os.system("pilight-send -p generic_label -i %s -l '%s'"%(data['pilight_timestamp_label'], datetime.datetime.now().timestamp()))
                except:
                    logger.error("Failed to update pilight")
                    pass

        else:
            logger.error("failed to get weather data")

        logger.debug("weather data updated")
    except:
        logger.error("failed to get response from knmi")

check_weather.last_sunpower = 0

if __name__ == '__main__':
    handler = RotatingFileHandler(
        '/var/log/weather_check.log',
        maxBytes=100000,
        backupCount=0)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)-22s - %(levelname)-8s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    handler_stdout = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler_stdout)
    logger.setLevel(logging.INFO)
    logger.info("Starting Olisto Weather checker")

    try:
        with open('config.json') as data_file:
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
