
resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.lambda_name}-httpapi"
  protocol_type = "HTTP"
  description   = "HTTP API for EC2 automation via Lambda"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ec2_api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "options_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "OPTIONS /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
  api_key_required = false
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw_allow" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
