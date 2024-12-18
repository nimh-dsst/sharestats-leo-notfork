provider "aws" {
  region = "us-east-1"  # Change to your desired region
}

resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "13.3"
  instance_class       = "db.t3.micro"
  name                 = "mydb"
  username             = "myuser"
  password             = "mypassword"
  parameter_group_name = "default.postgres13"
  skip_final_snapshot  = true

  # VPC and Subnet Group
  vpc_security_group_ids = [aws_security_group.postgres_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres_subnet.id
}

resource "aws_security_group" "postgres_sg" {
  name        = "allow_postgres"
  description = "Allow PostgreSQL inbound traffic"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Change this to restrict access
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "postgres_subnet" {
  name       = "postgres-subnet-group"
  subnet_ids = ["subnet-abc123", "subnet-def456"]  # Replace with your subnet IDs
}
