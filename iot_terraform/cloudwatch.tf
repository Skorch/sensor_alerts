
locals {
  moisture_sensor_alert_lambda_arn = "arn:aws:lambda:us-east-2:853166164242:function:aws-iot-sensor-gateway-dev-SensorAlert"
}


resource "aws_sns_topic" "moisture_sensor_alert_topic" {
  name = "moisture-sensor-alert-topic"
}

resource "aws_sqs_queue" "user_updates_queue" {
  name = "user-updates-queue"
}

resource "aws_sns_topic_subscription" "moisture_sensor_alert_lambda_target" {
  topic_arn = aws_sns_topic.moisture_sensor_alert_topic.arn
  protocol  = "lambda"
  endpoint  = local.moisture_sensor_alert_lambda_arn
}



resource "aws_cloudwatch_metric_alarm" "sensor_alarm" {
  for_each = toset(var.device_ids)

  alarm_name                = "moisture-${each.value}-alarm"
  comparison_operator       = "LessThanThreshold"
  evaluation_periods        = "2"
  metric_name               = "SensorRule_Moisture_${each.value}"
  namespace                 = "SensorRules"
  period                    = "120"
  statistic                 = "Average"
  threshold                 = "${var.moisture_alerts[each.value].threshold}"
  alarm_description         = "This metric monitors moisture level from a specific sensor"
  insufficient_data_actions = [aws_sns_topic.moisture_sensor_alert_topic.arn]
  ok_actions = [aws_sns_topic.moisture_sensor_alert_topic.arn]
  alarm_actions     = [aws_sns_topic.moisture_sensor_alert_topic.arn]
}

