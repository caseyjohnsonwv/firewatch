# create dynamo table for rides data
resource "aws_dynamodb_table" "rides_table" {
    name         = "qt-rides-${var.env_name}"
    billing_mode = "PAY_PER_REQUEST"
    hash_key     = "ride_id"

    attribute {
        name = "ride_id"
        type = "N"
    }
    attribute {
        name = "park_id"
        type = "N"
    }

    global_secondary_index {
        name            = "park_ride_ids"
        hash_key        = "park_id"
        projection_type = "KEYS_ONLY"
    }
}

# create dynamo table for user alerts
resource "aws_dynamodb_table" "alerts_table" {
    name         = "qt-alerts-${var.env_name}"
    billing_mode = "PAY_PER_REQUEST"
    hash_key     = "phone_number"

    attribute {
        name = "phone_number"
        type = "S"
    }
    attribute {
        name = "park_id"
        type = "N"
    }
    attribute {
        name = "ride_id"
        type = "N"
    }

    global_secondary_index {
        name            = "active_parks"
        hash_key        = "park_id"
        projection_type = "KEYS_ONLY"
    }

    global_secondary_index {
        name            = "user_alerts"
        hash_key        = "ride_id"
        projection_type = "INCLUDE"
        non_key_attributes = [
            "start_time",
            "end_time",
            "wait_time",
        ]
    }

    ttl {
        enabled        = true
        attribute_name = "ttl"
    }
}