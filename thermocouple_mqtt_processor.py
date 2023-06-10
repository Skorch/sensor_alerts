#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from ast import While
import json
import logging
from datetime import datetime, timezone

from config_mqtt import *
from config_thermocouple import *

from awscrt import io, mqtt
from awsiot import mqtt_connection_builder, iotshadow

from thermocouple_sensor import get_temps
import time

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

def send_message(mqtt_target, mqtt_topic, values):

    logger.debug(f"sending sensor reading '{values}'...")

    message = {"message" : values}
    # await asyncio.wrap_future(mqtt_target.publish(topic=mqtt_topic, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE))
    publish_future =  mqtt_target.publish(topic=mqtt_topic, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
    result = publish_future[0].result()
    logger.debug(f"{result}")
    logger.debug("Update request published.")

    


def event_template(sensor_type, sensor_id, system_id, sensor_ts, metric_name, metric_value): 
    return {
        "sensor_id": sensor_id,
        "sensor_type": sensor_type, 
        "system_id": system_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "timestamp": sensor_ts
    }

def process_data(data):

    create_message = lambda channel, value: event_template(SENSOR_TYPE, f"{SENSOR_TYPE}_{channel}", SYSTEM_ID, datetime.now(timezone.utc).isoformat(' '), "temperature", value)
    messages = [create_message(channel, value) for channel, value in data]

    for message_data in messages:
        logger.info(f"sending mqtt topic {MQTT_TOPIC} message {message_data}")
        send_message(mqtt_connection, MQTT_TOPIC, message_data)


def main():

    try:
        while True:
            try:
                data = get_temps()
                process_data(data)
            except Exception as e:
                logger.exception(e)
                
            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        logger.warn("shutting down")
        return
    
        # close_program() #Close other threads
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
    