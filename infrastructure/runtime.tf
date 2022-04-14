resource "heroku_app" "app" {
    name   = "queue-times-app-${var.env_name}"
    region = "us"
    buildpacks = [
        "heroku/python"
    ]
}


resource "heroku_addon" "database" {
    app_id = heroku_app.app.id
    plan   = "heroku-postgresql:hobby-dev"
}

resource "heroku_app_feature" "dyno_metadata" {
    app_id = heroku_app.app.id
    name   = "runtime-dyno-metadata"
}


resource "heroku_config" "app_config" {
    vars = {
        ENV_NAME    = var.env_name
        LOG_LEVEL   = "debug"
        MAX_THREADS = 1
    }

    sensitive_vars = {
        TWILIO_ACCOUNT_SID  = var.twilio_account_sid
        TWILIO_AUTH_TOKEN   = var.twilio_auth_token
        TWILIO_PHONE_NUMBER = var.twilio_phone_number
    }
}


resource "heroku_app_config_association" "config_attachment" {
  app_id         = heroku_app.app.id
  vars           = heroku_config.app_config.vars
  sensitive_vars = heroku_config.app_config.sensitive_vars
}


resource "null_resource" "deployment_script" {
    provisioner "local-exec" {
        interpreter = ["bash", "-c"]
        command     = "git push heroku $(git branch | grep \\* | cut -d \"*\" -f2 | sed 's/^ *//g'):main"
    }

    triggers = {
        # trigger on every apply
        deploy_time = timestamp(),
    }

    depends_on = [
        heroku_app_config_association.config_attachment,
        heroku_addon.database,
        heroku_app_feature.dyno_metadata,
    ]
}


output "twilio_webhook_target_url" {
    value = "https://${heroku_app.app.name}.herokuapp.com/live/twilio"
}