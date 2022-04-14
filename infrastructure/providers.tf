terraform {
    required_providers {
        heroku = {
            source  = "heroku/heroku"
            version = "~> 5.0"
        }
        null = {
            source = "hashicorp/null"
            version = "~> 3.0"
        }
    }
}