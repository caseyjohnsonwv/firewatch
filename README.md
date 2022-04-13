# queue-times-app
An SMS-based app leveraging the queue-times API to help maximize your theme park trip.

---

## Prerequisites
Before building or running anything, ensure the following are prepared:
1. **Python** - this application was developed for Python 3.8+
2. **Terraform** - all application infrastructre on AWS is managed via Terraform v0.13+
3. **Heroku** - account must be verified + CLI must be authenticated via `heroku login`
4. **Twilio** - a phone number capable of handling SMS must be provisioned

---

## Standing Up the Application
1. Clone this repository and `cd` into `/infrastructure`.
2. Create a new file `dev.tfvars` and add the below variables:
```
env_name = "dev"

twilio_account_sid  = ""
twilio_auth_token   = ""
twilio_phone_number = ""
```
3. Run `terraform init` and `terraform plan -var-file dev.tfvars` to preview the application infrastructure.
4. Run `terraform apply -var-file dev.tfvars` to stand up the application.
5. Copy the output `twilio_webhook_target_url` and update the webhook URL on Twilio for the provisioned phone number.
6. Send a sample text message to the provisioned phone number!