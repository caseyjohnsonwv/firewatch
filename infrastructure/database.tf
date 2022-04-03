# create dynamo table for rides data
resource "aws_dynamodb_table" "rides_table" {
    name           = "qt-rides-${var.env_name}"
    billing_mode   = "PROVISIONED"
    write_capacity = 10
    read_capacity  = 10
    hash_key       = "ride_id"

    attribute {
        name = "ride_id"
        type = "N"
    }
}

# create dynamo table for park data
resource "aws_dynamodb_table" "parks_table" {
    name           = "qt-parks-${var.env_name}"
    billing_mode   = "PROVISIONED"
    write_capacity = 10
    read_capacity  = 10
    hash_key       = "park_id"

    attribute {
        name = "park_id"
        type = "N"
    }
}

# create dynamo table for user alerts
resource "aws_dynamodb_table" "alerts_table" {
    name           = "qt-alerts-${var.env_name}"
    billing_mode   = "PROVISIONED"
    write_capacity = 10
    read_capacity  = 10
    hash_key       = "phone_number"

    attribute {
        name = "phone_number"
        type = "S"
    }
    attribute {
        name = "park_id"
        type = "N"
    }

    global_secondary_index {
        name              = "alerts_by_park"
        write_capacity    = 10
        read_capacity     = 10
        hash_key          = "park_id"
        projection_type   = "INCLUDE"
        non_key_attributes = [
            "ride_id",
            "start_time",
            "end_time",
            "wait_time",
        ]
    }
}