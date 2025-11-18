variable "lambda_name" {
  type    = string
  default = "ec2-manager-api"
}

variable "lambda_zip_path" {
  type    = string
  default = "../lambda.zip"
}