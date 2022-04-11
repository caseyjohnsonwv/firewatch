# VPC module
module "vpc" {
    source  = "terraform-aws-modules/vpc/aws"
    version = "3.11.4"
    name    = "qt-app-vpc"
    cidr    = "10.0.0.0/24"

    azs             = ["${var.aws_region}a", "${var.aws_region}b"]
    private_subnets = ["10.0.0.0/26", "10.0.0.64/26"]
    public_subnets  = ["10.0.0.128/26", "10.0.0.192/26"]

    enable_nat_gateway     = true
    single_nat_gateway     = false
    one_nat_gateway_per_az = true
    enable_vpn_gateway     = true
    enable_dns_hostnames   = true
    enable_dns_support     = true
}

# LOAD BALANCER SECURITY GROUP
resource "aws_security_group" "qt_app_lb_sg" {
    name = "qt-app-lb-sg-${var.env_name}"
    vpc_id = module.vpc.vpc_id

    ingress {
        from_port   = 5000
        to_port     = 5000
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

# ECS SERVICE SECURITY GROUP
resource "aws_security_group" "qt_app_ecs_service_sg" {
    name = "qt-app-ecs-service-sg-${var.env_name}"
    vpc_id = module.vpc.vpc_id

    ingress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port   = 0
        to_port     = 65535
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

# ECS LOGS
resource "aws_cloudwatch_log_group" "qt_app_logs" {
    name              = "qt-app-logs-${var.env_name}"
    retention_in_days = 1
}

# ECS CLUSTER
resource "aws_ecs_cluster" "qt_app_cluster" {
    name = "qt-app-cluster-${var.env_name}"

    configuration {
        execute_command_configuration {
            logging = "OVERRIDE"

            log_configuration {
                cloud_watch_log_group_name = aws_cloudwatch_log_group.qt_app_logs.name
            }
        }
    }
}

# ECS CAPACITY PROVIDER
resource "aws_ecs_cluster_capacity_providers" "qt_app_cluster_capacity" {
    cluster_name       = aws_ecs_cluster.qt_app_cluster.name
    capacity_providers = ["FARGATE"]

    default_capacity_provider_strategy {
        base              = 1
        weight            = 100
        capacity_provider = "FARGATE"
    }
}

# ECS TASK DEFINITION
resource "aws_ecs_task_definition" "qt_app_task_definition" {
    family                   = "qt-app-${var.env_name}"
    task_role_arn            = aws_iam_role.qt_app_role.arn
    execution_role_arn       = aws_iam_role.qt_app_role.arn
    requires_compatibilities = ["FARGATE"]
    network_mode             = "awsvpc"
    cpu                      = 256
    memory                   = 512
    container_definitions = jsonencode([
        {
            name      = "qt-app-container"
            image     = "${aws_ecr_repository.qt_app_ecr_repo.repository_url}:latest"
            cpu       = 256
            memory    = 512  
            essential = true
            portMappings = [
                {
                    containerPort = 5000
                    hostPort      = 5000
                }
            ]
            logConfiguration = {
                logDriver = "awslogs"
                options = {
                    awslogs-group = "${aws_cloudwatch_log_group.qt_app_logs.name}",
                    awslogs-region = "${var.aws_region}",
                    awslogs-stream-prefix = "qt-app-logs"
                }
            }
        }
    ])
}

# ECS SERIVCE
resource "aws_ecs_service" "qt_app_service" {
    name            = "qt-app-service-${var.env_name}"
    cluster         = aws_ecs_cluster.qt_app_cluster.id
    task_definition = aws_ecs_task_definition.qt_app_task_definition.arn
    wait_for_steady_state = true
    desired_count   = var.start_app_on_apply ? 1 : 0

    load_balancer {
        target_group_arn = aws_lb_target_group.qt_app_target_group.arn
        container_name   = "qt-app-container"
        container_port   = 5000
    }

    network_configuration {
        subnets = [
            module.vpc.public_subnets[0],
            module.vpc.public_subnets[1],
        ]
        security_groups = [
            aws_security_group.qt_app_ecs_service_sg.id,
        ]
        assign_public_ip = true
    }

    depends_on = [
        aws_lb_listener.qt_app_lb_forwarding,
        null_resource.qt_app_build_script,
    ]
}

# IAM ROLE FOR CONTAINER
resource "aws_iam_role" "qt_app_role" {
    name = "qt-app-task-role-${var.env_name}"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Sid    = ""
                Principal = {
                    Service = "ecs-tasks.amazonaws.com"
                }
            },
        ]
    })
}

# IAM POLICIES
resource "aws_iam_role_policy" "qt_app_role_policy" {
    name = "qt-app-policy-${var.env_name}"
    role = aws_iam_role.qt_app_role.id
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Sid      = "1"
                Effect   = "Allow"
                Resource = "*"
                Action = [
                    "dynamodb:*",
                    "ecr:*",
                    "logs:*",
                ]
            }
        ]
    })
}

# LOAD BALACNER
resource "aws_lb" "qt_app_lb" {
    name               = "qt-app-lb-${var.env_name}"
    security_groups    = [
        aws_security_group.qt_app_lb_sg.id
    ]
    subnets = [
        module.vpc.public_subnets[0],
        module.vpc.public_subnets[1],
    ]
}

# LOAD BALANCER TARGET GROUP
resource "aws_lb_target_group" "qt_app_target_group" {
    name                 = "qt-app-tg-${var.env_name}"
    port                 = 5000
    protocol             = "HTTP"
    target_type          = "ip"
    vpc_id               = module.vpc.vpc_id
    deregistration_delay = 0

    health_check {
        interval = 120
        timeout = 119
        path = "/"
        protocol = "HTTP"
        matcher = "200"
    }
}

# ATTACH TG TO LB
resource "aws_lb_listener" "qt_app_lb_forwarding" {
    load_balancer_arn = aws_lb.qt_app_lb.arn
    port              = 5000
    protocol          = "HTTP"

    default_action {
        type             = "forward"
        target_group_arn = aws_lb_target_group.qt_app_target_group.arn
    }
}

# ECR REPOSITORY
resource "aws_ecr_repository" "qt_app_ecr_repo" {
    name = "qt-app-repo-${var.env_name}"
}

# ECR PERMISSIONS
resource "aws_ecr_repository_policy" "ecs_image_pull_access" {
    repository = aws_ecr_repository.qt_app_ecr_repo.name
    policy = <<EOF
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Sid": "1",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "ecr:*"
    }
  ]
}
EOF
}

# ECR RETENTION POLICY
resource "aws_ecr_lifecycle_policy" "qt_app_ecr_retention_policy" {
    repository = aws_ecr_repository.qt_app_ecr_repo.name
    policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 2
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}

locals {
    parent_dir = abspath("${path.root}/../")
}

# BUILD AND PUSH DOCKER IMAGE
resource "null_resource" "qt_app_build_script" {
    provisioner "local-exec" {
        interpreter = ["bash", "-c"]
        command = <<EOF
aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
docker build -t ${aws_ecr_repository.qt_app_ecr_repo.repository_url}:latest -f ${local.parent_dir}/Dockerfile ${local.parent_dir}
docker push ${aws_ecr_repository.qt_app_ecr_repo.repository_url}:latest
EOF
    }

    triggers = {
        current_time = timestamp() # trigger on every apply
    }
    
    depends_on = [
        aws_ecr_repository.qt_app_ecr_repo
    ]
}