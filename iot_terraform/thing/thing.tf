#the thing

variable "thing_group" {
  type = string
}

variable "device_ids" {
  description = "DeviceOds"
  type        = list(string)
}

variable "hub_id" {
  description = "ID of the main hub"
  type        = string
}


resource "aws_iot_thing" "sensor_hub_thing" {
  name     = "${var.thing_group}-${var.hub_id}"
  thing_type_name = "${aws_iot_thing_type.sensor_hub.name}"
  attributes = {
    Name = "${var.thing_group}-${var.hub_id}"
  }
}

resource "aws_iot_thing_type" "sensor_hub" {
  name = "Sensor_Hub"
}

resource "aws_iot_thing_type" "moisture_sensor" {
  name = "Moisture_Sensor_Type"
}


resource "aws_iot_thing" "thing" {
  for_each = toset(var.device_ids)
  name     = "${aws_iot_thing.sensor_hub_thing.name}_${each.value}"
  thing_type_name = "${aws_iot_thing_type.moisture_sensor.name}"
  attributes = {
    Name = "${var.thing_group}-${each.value}"
  }
}

# resource "aws_iot_thing_type" "foo" {
#   name = "${var.thing_group}"
# }

#the thing certificate
resource "aws_iot_certificate" "thing-certificate" {
  active = true
}

#attch thing to certificate
resource "aws_iot_thing_principal_attachment" "thing-certificate-attachment" {
  for_each  = aws_iot_thing.thing
  principal = "${aws_iot_certificate.thing-certificate.arn}"
  thing     = "${each.value.name}"
}

#certificate iot policy
data "aws_iam_policy_document" "thing-policy-document" {
  statement {
    sid    = "1"
    effect = "Allow"
    actions = [
      "iot:*",
    ]
    resources = [
      "*",
    ]
  }
}

resource "aws_iot_policy" "thing-policy" {
  name   = "${var.thing_group}-policy"
  policy = "${data.aws_iam_policy_document.thing-policy-document.json}"
}

resource "aws_iot_policy_attachment" "thing-policy-attachment" {
  policy = "${aws_iot_policy.thing-policy.name}"
  target = "${aws_iot_certificate.thing-certificate.arn}"
}

#assume with certificate policy
data "aws_iam_policy_document" "thing-assume-with-cert-policy-document" {
  statement {
    sid    = "2"
    effect = "Allow"
    actions = [
      "iot:AssumeRoleWithCertificate",
    ]
    resources = [
      "${aws_iot_role_alias.thing-service-role-alias.arn}",
    ]
  }
}

resource "aws_iot_policy" "thing-assume-with-cert-policy" {
  name   = "${var.thing_group}-assume-with-cert-policy"
  policy = "${data.aws_iam_policy_document.thing-assume-with-cert-policy-document.json}"
}

resource "aws_iot_policy_attachment" "thing-assume-with-cert-policy-attachment" {
  policy = "${aws_iot_policy.thing-assume-with-cert-policy.name}"
  target = "${aws_iot_certificate.thing-certificate.arn}"
}


# resource "aws_iot_topic_rule" "thing-shadow-rule" {
#   name        = "ThingShadowRule"
#   description = "ThingShadowRule"
#   enabled     = true
#   sql         = "SELECT * , topic(3) as thingname , timestamp() as logtimestamp FROM '$aws/things/+/shadow/update'"
#   sql_version = "2016-03-23"

#   s3 {
#     bucket_name = "${aws_s3_bucket.thing-shadow-bucket.bucket}"
#     role_arn    = "${aws_iam_role.thing-shadow-rule-role.arn}"
#     key         = "things/shadow/$${parse_time(\"yyyy/MM/dd/HH\", timestamp(), \"UTC\")}/$${topic(3)}-$${timestamp()}.json"
#   }
# }

resource "aws_iot_topic_rule" "moisture_sensor_rule" {
  for_each = toset(var.device_ids)

  name        = "Moisture_Threshold_${each.value}"
  description = "Push moisture sensor values into a cloudwatch metric"
  enabled     = true
  sql         = "SELECT current.state.reported.moisture as moisture, topic(3) as thing_id, current.state.desired.display_name as display_name FROM '$aws/things/+/shadow/update/documents' WHERE regexp_matches(topic(3), '${each.value}$')"
  sql_version = "2016-03-23"

  cloudwatch_metric {
    metric_name = "${each.key}"
    metric_namespace = "SensorRule_Moisture_${each.value}"
    metric_unit = "Percent"
    metric_value = "$${current.state.reported.moisture}"
    role_arn = "${aws_iam_role.iot_humidity_sensor_metric_update_role.arn}"
  }

  # error_action {
  #   sns {
  #     message_format = "RAW"
  #     role_arn       = aws_iam_role.role.arn
  #     target_arn     = aws_sns_topic.myerrortopic.arn
  #   }
  # }
}