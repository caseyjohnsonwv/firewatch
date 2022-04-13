variable "env_name" {
    type = string
}

variable "deployment_commit_message" {
    type = string
}

variable "twilio_account_sid" {
    type = string
    sensitive = true
}

variable "twilio_auth_token" {
    type = string
    sensitive = true
}

variable "twilio_phone_number" {
    type = string
    sensitive = true
}