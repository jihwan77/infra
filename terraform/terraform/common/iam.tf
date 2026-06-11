resource "aws_iam_role" "lab_instance_role" {
  name = "lab-ec2-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = { Service = "ec2.amazonaws.com" },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lab_cloudwatch_policy" {
  role       = aws_iam_role.lab_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "lab_instance_profile" {
  name = "lab-ec2-instance-profile"
  role = aws_iam_role.lab_instance_role.name
}