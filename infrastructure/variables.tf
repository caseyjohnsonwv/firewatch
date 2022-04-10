variable "env_name" {
    type = string
}

variable "aws_account_id" {
    type = string
}

variable "aws_profile" {
    type = string
    default = "default"
}

variable "aws_region" {
    type = string
    default = "us-east-2"
}

variable "start_app_on_apply" {
    type = bool
    default = false
}