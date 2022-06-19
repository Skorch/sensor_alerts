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

from config import *

from ecowitt_data import DataProcessor

from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder, iotshadow

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

mqtt_connection = None

# TODO:  understand this
io.init_logging(getattr(io.LogLevel, io.LogLevel.Info.name), 'stderr')


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted. error: {error}")


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Connection resumed. return_code: {return_code} session_present: {session_present}")


async def change_shadow_value(mqtt_connection, thing_name, values):

    print("Updating reported shadow value to '{}'...".format(values))
    request = iotshadow.UpdateShadowRequest(
        thing_name=thing_name,
        state=iotshadow.ShadowState(
            reported=values
        )
    )
    shadow_client = iotshadow.IotShadowClient(mqtt_connection)

    await asyncio.wrap_future(shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE))

    logger.info("Update request published.")


async def process_data(mqtt_connection, data, passkey):

    thing_name = f'SensorHub_{passkey}'
    

    soil_sensors = {}
    shadow_update = {}
    for key in data:
        if 'soil' in key:
            match = re.match('^soil(?P<metric>[A-Za-z]+)(?P<sensor_number>\d+)$', key)
            sensor_number = f"soil{match.group('sensor_number')}"
            sensor = soil_sensors.get(sensor_number, {})
            sensor[match.group('metric')] = data[key]
            soil_sensors[sensor_number] = sensor
        else:
            shadow_update[key] = data[key]

    flatten_soil = lambda x: {**soil_sensors[x], **{"id": x} }
    shadow_update["soil_sensors"] = soil_sensors
    shadow_update["soil_sensors_array"] = list(( flatten_soil(sensor) for sensor in soil_sensors ))

    await change_shadow_value(mqtt_connection, thing_name, shadow_update)

    for sensor in soil_sensors:
        soil_update = soil_sensors[sensor]
        soil_thing = f"{thing_name}_{sensor}"
        await change_shadow_value(mqtt_connection, soil_thing, soil_update)



