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

from config import *

from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder, iotshadow

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)


received_count = 0
received_all_event = threading.Event()

rtl_433_cmd = "/usr/local/bin/rtl_433 -f 915M -R142 -Y classic -s 250k -g49 -Fjson"

important_rtl_output_re = re.compile("^(Found|Tuned)")

class LockedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.shadow_value = None
        self.disconnect_called = False

locked_data = LockedData()



# TODO:  understand this
io.init_logging(getattr(io.LogLevel, io.LogLevel.Info.name), 'stderr')


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    logger.error(f"Connection interrupted. error: {error}")


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(f"Connection resumed. return_code: {return_code} session_present: {session_present}")

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        logger.warning("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        logger.info(f"Resubscribe results: {resubscribe_results}")

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    logger.debug(f"Received message from topic '{topic}': {payload}")
    global received_count
    received_count += 1
    # TOOD:  remove
    if received_count == -1:
        received_all_event.set()

def on_publish_update_shadow(future):
    #type: (Future) -> None
    try:
        future.result()
        logger.info("Update request published.")
    except Exception as e:
        logger.error("Failed to publish update request.")
        exit(e)

def change_shadow_value(thing_name, values):
    with locked_data.lock:
        # if locked_data.shadow_value == values:
        #     print("Local value is already '{}'.".format(values))
        #     return

        print("Changed local shadow value to '{}'.".format(values))
        locked_data.shadow_value = values

    print("Updating reported shadow value to '{}'...".format(values))
    request = iotshadow.UpdateShadowRequest(
        thing_name=thing_name,
        state=iotshadow.ShadowState(
            reported=values
        )
    )
    future = shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    future.add_done_callback(on_publish_update_shadow)


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


    # # Subscribe
    # logger.info("Subscribing to topic '{MQTT_TOPIC}'...")
    # subscribe_future, packet_id = mqtt_connection.subscribe(
    #     topic=MQTT_TOPIC,
    #     qos=mqtt.QoS.AT_LEAST_ONCE,
    #     callback=on_message_received)

    # subscribe_result = subscribe_future.result()
    # logger.info("Subscribed with {}".format(str(subscribe_result['qos'])))

    # Start RTL433 listener
    logger.info("Starting RTL433")
    rtl433_proc = subprocess.Popen(rtl_433_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    logger.debug("...")



    while True:
        logger.info("polling")
        val = rtl433_proc.poll()
        if val is not None:
            logger.info("RTL433 exited with code " + str(rtl433_proc.poll()))
            sys.exit(rtl433_proc.poll())

        logger.info(f"poll: {val}")

        shadow_client = iotshadow.IotShadowClient(mqtt_connection)

        for message in iter(rtl433_proc.stdout.readline, '\n'):

            try:
                message_data = json.loads(message)
                logger.info(f"message result: {message_data}")
                change_shadow_value(AWS_THING_NAME, message_data)
            except ValueError as e:
            
                continue
                # print(f"Publishing message to topic '{MQTT_TOPIC}': {device_shadow_state}")
                # mqtt_connection.publish(topic=MQTT_TOPIC, payload=device_shadow_state, qos=mqtt.QoS.AT_LEAST_ONCE)



        time.sleep(1)
