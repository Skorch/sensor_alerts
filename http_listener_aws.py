#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import logging
import threading
import asyncio
import io
import json

import http_aws_iot_shadow_processor as iot_processor
import http_aws_mqtt_processor as mqtt_processor

from config import *

from ecowitt_data import DataProcessor

from aiohttp import web

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

def setup():
    iot_processor.setup_connection()
    mqtt_processor.setup_connection()

async def async_publish_payload(request: web.Request):

 
    payload = dict(await request.post())

    logger.debug("Received data from Ecowitt device: %s", payload)

    data_processor = DataProcessor(payload, UNIT_SYSTEM)
    data = data_processor.generate_data()

    passkey = payload.get("PASSKEY")
    await iot_processor.process_data(data, passkey)
    await mqtt_processor.process_data(data, passkey)


def main():
    setup()

    app = web.Application()
    app.add_routes([web.post(AIOHTTP_ENDPOINT, async_publish_payload)])

    web.run_app(app, port=AIOHTTP_PORT)

async def test(payload_path):
    setup()


    payload_file = io.open(payload_path)
    payload = json.load(payload_file)

    logger.debug("Received data from Ecowitt device: %s", payload)

    data_processor = DataProcessor(payload, UNIT_SYSTEM)
    data = data_processor.generate_data()

    passkey = payload.get("PASSKEY")
    await iot_processor.process_data(data, passkey)
    await mqtt_processor.process_data(data, passkey)


    

if __name__ == '__main__':

    main()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(test("./sample_events/basic.txt"))
    # asyncio.run(test("./sample_events/basic.txt"))
    