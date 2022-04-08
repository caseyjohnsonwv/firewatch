# VPC
resource "aws_vpc" "qt_app_vpc" {
    cidr_block = "10.0.0.0/24"
    tags = {
        Name = "qt-app-vpc-${var.env_name}"
    }
}

# GATEWAY
resource "aws_internet_gateway" "qt_app_igw" {
    vpc_id = aws_vpc.qt_app_vpc.id
    tags = {
        Name = "qt-app-igw-${var.env_name}"
    }
}

# SUBNET 1
resource "aws_subnet" "qt_app_vpc_subnet_1" {
    vpc_id     = aws_vpc.qt_app_vpc.id
    cidr_block = "10.0.0.0/25"
    availability_zone = "us-east-2a"
}

# SUBNET 2
resource "aws_subnet" "qt_app_vpc_subnet_2" {
    vpc_id     = aws_vpc.qt_app_vpc.id
    cidr_block = "10.0.0.128/25"
    availability_zone = "us-east-2b"
}

# SECURITY GROUP
resource "aws_security_group" "qt_app_lb_sg" {
    name = "qt-app-lb-sg-${var.env_name}"
    vpc_id = aws_vpc.qt_app_vpc.id

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

# ECS LOGS
resource "aws_cloudwatch_log_group" "qt_app_logs" {
    name              = "qt-app-logs-${var.env_name}"
    retention_in_days = 3
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
        }
    ])
}

# ECS SERIVCE
resource "aws_ecs_service" "qt_app_service" {
    name            = "qt-app-service-${var.env_name}"
    cluster         = aws_ecs_cluster.qt_app_cluster.id
    task_definition = aws_ecs_task_definition.qt_app_task_definition.arn
    desired_count   = var.start_app_on_apply ? 1 : 0

    load_balancer {
        target_group_arn = aws_lb_target_group.qt_app_target_group.arn
        container_name   = "qt-app-container"
        container_port   = 5000
    }

    network_configuration {
        subnets = [
            aws_subnet.qt_app_vpc_subnet_1.id,
            aws_subnet.qt_app_vpc_subnet_2.id,
        ]
        security_groups = [
            aws_security_group.qt_app_lb_sg.id,
        ]
        assign_public_ip = true
    }

    depends_on = [
        aws_lb_listener.qt_app_lb_forwarding,
        null_resource.qt_app_build_script,
        aws_ecr_repository_policy.ecs_image_pull_access,
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
                Sid       = "1"
                Effect    = "Allow"
                Resource  = "arn:aws:dynamodb:::*"
                Action = [
                    "dynamodb:DeleteItem",
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ]
            },
            {
                Sid       = "2"
                Effect    = "Allow"
                Resource  = "arn:aws:ecr:::*"
                Action    = "ecr:*"
            }
        ]
    })
}

# LOAD BALACNER
resource "aws_lb" "qt_app_lb" {
    name               = "qt-app-lb-${var.env_name}"
    load_balancer_type = "application"
    security_groups    = [
        aws_security_group.qt_app_lb_sg.id
    ]
    subnets = [
        aws_subnet.qt_app_vpc_subnet_1.id,
        aws_subnet.qt_app_vpc_subnet_2.id,
    ]
    depends_on = [
        aws_internet_gateway.qt_app_igw,
    ]
}

# LOAD BALANCER TARGET GROUP
resource "aws_lb_target_group" "qt_app_target_group" {
    name        = "qt-app-tg-${var.env_name}"
    port        = 5000
    protocol    = "HTTP"
    target_type = "ip"
    vpc_id      = aws_vpc.qt_app_vpc.id
    depends_on = [
        aws_lb.qt_app_lb,
    ]
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
      "Principal": {
        "AWS": "arn:aws:iam::${var.aws_account_id}:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS"
      },
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