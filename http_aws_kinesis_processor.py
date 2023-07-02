#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import re
import logging
import boto3
from datetime import datetime

from config import *
from credentials import *

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)

kinesis_client = boto3.client(
    'firehose',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def event_template(sensor_type, sensor_id, system_id, sensor_ts, metric_name, metric_value): 
    return {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type, 
        "system_id": system_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "timestamp": sensor_ts
    }

def process_data(data, passkey):

    logger.info(f"received data {data}")

    sensor_ts = data["dateutc"]

    soil_sensors = []
    system_id = f"soil_{passkey}"

    for key in data:
        if 'soil' in key:
            match = re.match('^soil(?P<metric>[A-Za-z]+)(?P<sensor_number>\d+)$', key)
            sensor_number = f"soil{match.group('sensor_number')}"
            metric_name = match.group('metric')
            metric_value = data[key]
            sensor_id = sensor_number
            soil_sensors.append(event_template("soil_moisture", sensor_id, system_id, sensor_ts, metric_name, metric_value))

        if key in ['tempinf', 'humidityin', 'baromrelin', 'baromabsin']:
            metric_name = key
            metric_value = data[key]
            sensor_id = f"hub_{passkey}"
            soil_sensors.append(event_template("soil_moisture", sensor_id, system_id, sensor_ts, metric_name, metric_value))

    # Batch data for sending
    batch_data = []
    for message_data in soil_sensors:
        logger.info(f"sending kinesis message {message_data}")
        batch_data.append({
            'Data': json.dumps({"message": message_data})
        })

    if batch_data:
        response = kinesis_client.put_record_batch(
            DeliveryStreamName=KINESIS_STREAM_NAME,
            Records=list(batch_data)
        )        
        # kinesis_client.put_recordbatch(StreamName=KINESIS_STREAM_NAME, Records=batch_data)

        logger.debug(f"{response}")
        logger.debug("Update batch request published.")

if __name__ == "__main__":
    test_data = {
        'PASSKEY': '<UUID>', 
        'stationtype': 'GW1000B_V1.6.8', 
        'dateutc': '2022-06-19 00:42:32', 
        'tempinf': '72.5', 
        'humidityin': '52', 
        'baromrelin': '29.692', 
        'baromabsin': '29.692', 
        'soilmoisture1': '47', 
        'soilmoisture4': '52', 
        'soilbatt1': '1.3', 
        'soilbatt4': '1.4', 
        'freq': '915M', 
        'model': 'GW1000_Pro'
    }
    
    process_data(test_data, 'your-passkey')
