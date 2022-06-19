#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import subprocess
import sys
import time
import os
import json
import re
import logging
import threading
import asyncio
from datetime import datetime

from config_mqtt import *

from ecowitt_data import DataProcessor

from awscrt import io, mqtt
from awsiot import mqtt_connection_builder, iotshadow

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)


# TODO:  understand this
io.init_logging(getattr(io.LogLevel, io.LogLevel.Info.name), 'stderr')


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted. error: {error}")


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Connection resumed. return_code: {return_code} session_present: {session_present}")

async def send_message(mqtt_target, mqtt_topic, values):

    logger.debug(f"sending sensor reading '{values}'...")

    message = {"message" : values}
    # await asyncio.wrap_future(mqtt_target.publish(topic=mqtt_topic, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE))
    publish_future =  mqtt_target.publish(topic=mqtt_topic, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
    result = publish_future[0].result()
    logger.debug(f"{result}")
    logger.debug("Update request published.")


async def process_data(mqtt_connection, data, passkey):


    # Data comes in the form:
    # {
    #     'PASSKEY': '<UUID>', 
    #     'stationtype': 'GW1000B_V1.6.8', 
    #     'dateutc': '2022-06-19 00:42:32', 
    #     'tempinf': '72.5', 
    #     'humidityin': '52', 
    #     'baromrelin': '29.692', 
    #     'baromabsin': '29.692', 
    #     'soilmoisture1': '47', 
    #     ....
    #     'soilmoisture4': '52', 
    #     'soilbatt1': '1.3', 
    #     ....
    #     'soilbatt4': '1.4', 
    #     'freq': '915M', 
    #     'model': 'GW1000_Pro'
    # }    
    # pivot this into a series of 'soilX' messages, and then everything else as part of an envionrmnetal sensor
    sensor_ts = datetime.now().isoformat()
    soil_sensors = {}

    environment_sensor = {
        "ts": sensor_ts
    }

    for key in data:
        if 'soil' in key:
            match = re.match('^soil(?P<metric>[A-Za-z]+)(?P<sensor_number>\d+)$', key)
            sensor_number = f"soil{match.group('sensor_number')}"
            sensor = soil_sensors.get(sensor_number, {})
            sensor[match.group('metric')] = data[key]
            sensor["ts"] = sensor_ts
            sensor["type"] = "soil_moisture"
            sensor["system_id"] = f"soil_{passkey}"
            soil_sensors[sensor_number] = sensor

        if key in ['tempinf', 'humidityin', 'baromrelin', 'baromabsin']:
            # look for certain sensor readings
            
            environment_sensor[key] = data[key]


    flatten_soil = lambda x: {**soil_sensors[x], **{"id": x} }
    
    
    # output:
    # {
    #     "system_id", "soil_PASSKEY",
    #     "id": "soil1",
    #     "moisture": "1",
    #     "batt": "1",
    #     "ts": "timestamp",
    #     "type": "soil_moisture"
    # }

    sensor_message_data_list = list(( flatten_soil(sensor) for sensor in soil_sensors ))
# TODO: environment sensor either goes on a different topic or need to include sensor type
    # sensor_message_data_list += environment_sensor

    for message_data in sensor_message_data_list:
        logger.info(f"sending mqtt topic {MQTT_TOPIC} message {message_data}")
        await send_message(mqtt_connection, MQTT_TOPIC, message_data)

