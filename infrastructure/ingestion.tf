# create s3 landing zone for all json data
resource "aws_s3_bucket" "qt_data" {
    bucket = "qt-data-${var.env_name}"
    force_destroy = true
}

# configure lifecycle policies on bucket
resource "aws_s3_bucket_lifecycle_configuration" "purge_policy" {
    bucket = aws_s3_bucket.qt_data.bucket
    rule {
        id     = "qt-data-${var.env_name}-wait-times-purge-policy"
        status = "Enabled"    
        expiration {
            days = 1
        }
        filter {
            prefix = "wait-times/"
        }
    }
    rule {
        id     = "qt-data-${var.env_name}-parks-data-purge-policy"
        status = "Enabled"    
        expiration {
            days = 7
        }
        filter {
            prefix = "parks.json"
        }
    }
}

# create queue for async updates to dynamo tables
resource "aws_sqs_queue" "wait_times_update_queue" {
    name = "qt-data-wait-times-update-queue-${var.env_name}"
    policy = data.aws_iam_policy_document.sqs_policy.json
}

# configure s3 event upload policy on queue
data "aws_iam_policy_document" "sqs_policy" {
    statement {
        actions = [
            "sqs:SendMessage",
        ]
        resources = [
            "arn:aws:sqs:::*"
        ]
    }
}

# configure s3 bucket to upload to queue
resource "aws_s3_bucket_notification" "wait_times_upload_event" {
    bucket = aws_s3_bucket.qt_data.id
    queue {
        queue_arn     = aws_sqs_queue.wait_times_update_queue.arn
        events        = ["s3:ObjectCreated:*"]
        filter_prefix = "wait-times/"
        filter_suffix = ".json"
    }
}