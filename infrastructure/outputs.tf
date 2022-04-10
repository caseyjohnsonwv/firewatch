# TWILIO WEBHOOK TARGET URL
data "aws_network_interface" "qt_app_eni" {
    filter {
        name   = "vpc-id"
        values = [module.vpc.vpc_id]
    }
    filter {
        name   = "group-id"
        values = [aws_security_group.qt_app_ecs_service_sg.id]
    }
    depends_on = [
        aws_ecs_service.qt_app_service,
    ]
}
output "twilio_webhook_target_url" {
    value = "http://${data.aws_network_interface.qt_app_eni.association[0].public_dns_name}:5000/alerts/twilio"
    description = "Paste this into Twilio under the phone number's incoming SMS webhook URL."
}