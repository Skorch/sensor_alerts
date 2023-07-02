
# Config section
# Fill in the next 2 lines if your MQTT server expected authentication
AWS_CLIENT_ID="853166164242"
AWS_ROOT_CA="../aws_iot/aws.rc"
AWS_KEY_PATH="../aws_iot/SensorHub_4541DDAA20550D40566163953AA78D9C-private.pem.key"
AWS_CERT_PATH="../aws_iot/SensorHub_4541DDAA20550D40566163953AA78D9C-certificate.pem.crt"
# AWS_THING_NAME="Fineoffset-WH51-0011d2"
MQTT_USER=""
MQTT_PASS=""
MQTT_HOST="a3gki318s2zulg-ats.iot.us-east-2.amazonaws.com"
MQTT_PORT=433
# MQTT_TOPIC="$aws/things/{thing_name}/shadow/update"
MQTT_QOS=0
DEBUG=True # Change to True to log all MQTT messages

AIOHTTP_ENDPOINT = "/data/report/"
AIOHTTP_PORT = 8888
UNIT_SYSTEM = 'metric'
# End config section


