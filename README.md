# queue-times-app
An SMS-based app leveraging the queue-times API to help maximize your theme park trip.

---

## Prerequisites
Before building or running anything, ensure the following are prepared:
1. **Python** - this application was developed for Python 3.8+
2. **Docker** - the Docker daemon must be running locally to build the application
3. **Terraform** - all application infrastructre on AWS is managed via Terraform v0.13+
4. **AWS CLI** - including a credentials file `~/.aws/credentials` with a profile
5. **Twilio** - a phone number capable of handling SMS must be provisioned

---

## Standing Up the Application
1. Clone this repository and `cd` into `/infrastructure`.
2. Create a new file `dev.tfvars` and add the below variables:
```
env_name = "dev"

aws_account_id = ""
aws_profile    = ""
aws_region     = ""

start_app_on_apply = true
```
3. Create a new file `.env` and populate the below variables:
```
ENV_NAME=dev
LOG_LEVEL=info

API_HOST=0.0.0.0
API_PORT=5000
MAX_THREADS=8

AWS_DEFAULT_REGION=

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```
4. Run `terraform init` and `terraform plan -var-file dev.tfvars` to preview the application infrastructure.
5. Run `terraform apply -var-file dev.tfvars` to stand up the application.
6. Copy the output `twilio_webhook_target_url` and update the webhook URL on Twilio for the provisioned phone number.
7. Send a sample text message to the provisioned phone number!