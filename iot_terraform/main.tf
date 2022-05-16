
variable "region" {
  type    = string
  default = "us-east-2"
}

variable "AWS_ACCESS_KEY_ID" {
    type = string  
}
variable "AWS_SECRET_ACCESS_KEY" {
    type = string  
}

#since terraform is not supporting thing group yet, we will user this variable as prefix
variable "thing_group" {
  type = string
  default="moisture_sensor"
}

variable "organization_name" {
  type = string
  default = "basedata"
}

variable "hub_id" {
  type = string
  default = "4541DDAA20550D40566163953AA78D9C"
}

variable "device_ids" {
  description = "Create thing for users"
  type        = list(string)
  default = ["moisture_sensor1", "moisture_sensor2"]
}

variable "moisture_alerts" {
  description = "Alet thresholds for devices"
  type = map(
    object({
      threshold = string
      }))
  default = {
    moisture_sensor1 = {
      threshold = 30
    },
    moisture_sensor2 = {
      threshold = 30
    },
  }
}

provider "aws" {
  # Configuration options
  region = "${var.region}"
  access_key = "${var.AWS_ACCESS_KEY_ID}"
  secret_key = "${var.AWS_SECRET_ACCESS_KEY}"
}

terraform {
  # backend "s3" {
  #   bucket = "jff-terraform-eu-central-1"
  #   key    = "e-ticket/terraform.tfstate"
  #   region = "eu-central-1"
  # }
}


module "thing" {
  source            = "./thing"
  outputs_path      = "${path.module}/outputs"
  region            = "${var.region}"
  thing_group       = "${var.thing_group}"
  hub_id            = "${var.hub_id}"
  device_ids        = "${var.device_ids}"
  organization_name = "${var.organization_name}"
}
