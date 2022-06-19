#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import logging
import threading
import asyncio
from io import open
import json

import http_aws_iot_shadow_processor as iot_processor
import http_aws_mqtt_processor as mqtt_processor

from config import *

from ecowitt_data import DataProcessor

from aiohttp import web
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder, iotshadow

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted. error: {error}")


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Connection resumed. return_code: {return_code} session_present: {session_present}")

async def async_publish_payload(request: web.Request):

 
    payload = dict(await request.post())

    logger.debug("Received data from Ecowitt device: %s", payload)

    data_processor = DataProcessor(payload, UNIT_SYSTEM)
    data = data_processor.generate_data()

    passkey = payload.get("PASSKEY")
    await iot_processor.process_data(mqtt_connection, data, passkey)
    await mqtt_processor.process_data(mqtt_connection, data, passkey)


def main():

    app = web.Application()
    app.add_routes([web.post(AIOHTTP_ENDPOINT, async_publish_payload)])

    web.run_app(app, port=AIOHTTP_PORT)

async def test(payload_path):


    payload_file = open(payload_path)
    payload = json.load(payload_file)

    logger.debug("Received data from Ecowitt device: %s", payload)

    data_processor = DataProcessor(payload, UNIT_SYSTEM)
    data = data_processor.generate_data()

    passkey = payload.get("PASSKEY")
    await iot_processor.process_data(mqtt_connection, data, passkey)
    await mqtt_processor.process_data(mqtt_connection, data, passkey)


    

if __name__ == '__main__':

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=MQTT_HOST,
            cert_filepath=AWS_CERT_PATH,
            pri_key_filepath=AWS_KEY_PATH,
            client_bootstrap=client_bootstrap,
            ca_filepath=AWS_ROOT_CA,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=AWS_CLIENT_ID,
            clean_session=False,
            keep_alive_secs=6)

    logger.info(f"Connecting to {MQTT_HOST} with client ID '{AWS_CLIENT_ID}'...")

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    logger.info("Connected!")



    main()
    # test("./sample_events/basic.txt")
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(test("./sample_events/basic.txt"))
    # asyncio.run(test("./sample_events/basic.txt"))
    