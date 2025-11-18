resource "aws_lambda_function" "ec2_api" {
  function_name    = "ec2-lambda"
  filename         = var.lambda_zip_path
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 300
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = {
      REGION            = "us-east-1"
      AMI_ID            = "ami-08982f1c5bf93d976"
    }
  }
}