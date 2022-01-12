#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import subprocess
import sys
import time
import paho.mqtt.client as mqtt
import os
import json
import re
import logging

from config import *

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)


rtl_433_cmd = "/usr/local/bin/rtl_433 -f 915M -R142 -Y classic -s 250k -g49"

important_rtl_output_re = re.compile("^(Found|Tuned)")

# Define MQTT event callbacks
def on_connect(client, userdata, flags, rc):
    connect_statuses = {
        0: "Connected",
        1: "incorrect protocol version",
        2: "invalid client ID",
        3: "server unavailable",
        4: "bad username or password",
        5: "not authorised"
    }
    logger.error("MQTT: " + connect_statuses.get(rc, "Unknown error"))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warn("Unexpected disconnection")
    else:
        logger.info("Disconnected")

def on_message(client, obj, msg):
    logger.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(client, obj, mid):
    logger.info("Pub: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    logger.log(level, string)

# Setup MQTT connection
mqttc = mqtt.Client()

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect

if DEBUG:
    logger.info("Debugging messages enabled")
    mqttc.on_log = on_log
    mqttc.on_message = on_message
    mqttc.on_publish = on_publish

if MQTT_PASS:
    logger.info("Connecting with authentication")
    mqttc.username_pw_set(MQTT_USER, password=MQTT_PASS)
else:
    logger.info("Connecting without authentication")

mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
logger.info("starting loop")
mqttc.loop_start()
logger.info("loop started")
# Start RTL433 listener
logger.info("Starting RTL433")
rtl433_proc = subprocess.Popen(rtl_433_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
logger.warn("...")
while True:
    logger.into("polling")
    val = rtl433_proc.poll()
    if val is not None:
        logger.info("RTL433 exited with code " + str(rtl433_proc.poll()))
        sys.exit(rtl433_proc.poll())

    logger.info(f"poll: {val}")
    for line in iter(rtl433_proc.stdout.readline, '\n'):
        logger.debug("RTL: " + line)
        if important_rtl_output_re.match(line):
            logger.info(line)

        if rtl433_proc.poll() is not None:
            logger.info("RTL433 exited with code " + str(rtl433_proc.poll()))
            sys.exit(rtl433_proc.poll())

        if "time" in line:
            mqttc.publish(MQTT_TOPIC, payload=line, qos=MQTT_QOS, retain=True)
            json_dict = json.loads(line)
            for item in json_dict:
                value = json_dict[item]
                if item == "model":
                    subtopic = value
                if item == "id":
                    subtopic += "/" + str(value)

            for item in json_dict:
                value = json_dict[item]
                if not "model" in item:
                    mqttc.publish(MQTT_TOPIC+"/"+subtopic+"/"+item, payload=value, qos=MQTT_QOS, retain=True)