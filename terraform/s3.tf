# AWS Provider Configuration
provider "aws" {
  region = "us-east-1"
}

# Create S3 Bucket for PUT Project
resource "aws_s3_bucket" "put_files" {
  bucket = "put-files-unique-12345"  # Ensure this is globally unique
  acl    = "private"  # Keep it private for security

  tags = {
    Name        = "PUT Files Bucket"
    Environment = "Development"
    Project     = "PUT"
  }
}

# Bucket Policy for Access Control
resource "aws_s3_bucket_policy" "put_files_policy" {
  bucket = aws_s3_bucket.put_files.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.put_files.arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = "YOUR_AWS_ACCOUNT_ID"  # Replace with your AWS Account ID
          }
        }
      }
    ]
  })
}

# Outputs
output "bucket_name" {
  description = "The name of your S3 bucket"
  value       = aws_s3_bucket.put_files.bucket
}

output "bucket_arn" {
  description = "The ARN of your bucket"
  value       = aws_s3_bucket.put_files.arn
}
