# Lambda function to control EC2 instances
This project demonstrates how to manage AWS EC2 instances using AWS Lambda, API Gateway, and a Flask web app with a user-friendly Bootstrap UI

## Features

Create instance 
select instance from dropdown and perform operations like stop,terminate and start 
Simple Flask web interface with action buttons and drop down which list all instances available
Responsive UI using HTML, CSS, and Bootstrap

## Architecture

Client (Flask Web UI/Postman) → API Gateway → Lambda → EC2

## Setup Steps

1. Create Lambda Function
Attach an IAM role with policies to manage EC2 instances.
2. Create API Gateway
Set up endpoints for each EC2 action and for authorizations use aws iam.
3. Test the Setup
Use Postman, the Flask Web UI, or Lambda test events.

## API Base URL:
https://6xzeq28mbi.execute-api.us-east-1.amazonaws.com/stg


## Flask Demo Web UI

- Run `python app.py` under your project folder path
- Open [http://localhost:5000/ec2] in your browser
- Use  **Create**,**Start**, **Stop**, and **Terminate** buttons to control your EC2 instance
- Success and result messages will be shown on the page

## File Structure
lambda_handler.py – Lambda function code
app.py – Flask web app
requirements.txt – All required libraries are listed in requirements.txt. Install them using "pip" 
docs/ – Screenshots and architecture diagram



## Lambda functionality 
1. Create Button- One new instance will get created 
2. Stop Button-   Instance selected from dropdown will be stopped 
3. Start Button - Instance selected from dropdown will get started if state is other than running ,   Otherwise it will show a message "instance is already running"
4. Terminate Button - selected Instance will get terminated  

## EC2 Action Validations (Handled in Lambda)

## create
Creates a new EC2 instance using predefined AMI, instance type, key pair, and security group.
Waits until the instance is running.
Returns:
instance_id
public_ip
username (default: ec2-user)
key_name used for SSH 
ssh command




## start
Requires instance_id.
Checks current state of the instance:
If stopped: starts the instance.
If running: returns message that instance is already running.
If stopping: returns message to retry later.
If shutting-down or terminated: returns error that instance cannot be started.
Any other state: returns error with current state.




## stop
Requires instance_id.
Checks current state of the instance:
If running: stops the instance.
If stopped: returns message that instance is already stopped.
If terminated: returns error that instance cannot be stopped.
Any other state: returns error with current state.



## terminate
Requires instance_id.
Checks current state of the instance:
If terminated: returns error that instance is already terminated.
Otherwise: terminates the instance.




## Common Error Handling

If action is missing or invalid: returns error "Invalid action. Use start, stop, terminate, or create."
If instance_id is missing for actions that require it: returns error "Missing 'instanceId' for <action>".

Any unexpected exception: returns a 500 error with the exception message.



## Implmentation with terraform and jenkins 

## 📦 Project Structure

```
Jenkins/
├── terraform/                # Terraform IaC files
│   ├── api.tf                # API Gateway setup
│   ├── iam.tf                # IAM roles and policies
│   ├── lambda.tf             # Lambda function configuration
│   ├── outputs.tf            # Terraform outputs
│   ├── provider.tf           # AWS provider setup
│   ├── variables.tf          # Input variables
│   ├──src
│    ├── app.py                    # Flask UI for EC2 control
│    ├── lambda_api_runner.py      # Jenkins runner script
│    ├── lambda_handler.py         # Lambda function code
├── lambda.zip                     # Packaged Lambda deployment
├── screenshots
├── Readme.md
|--- requirement.txt
```

---

## 🛠️ Prerequisites

- AWS CLI configured with credentials
- Terraform installed
- Python 3.12
- Jenkins installed and configured
- IAM user with EC2, Lambda, Secrets Manager permissions

---

## 🚀 How It Works

### Lambda Function
- Handles EC2 actions: create, start, stop, terminate, list
- Stores SSH private key in Secrets Manager
- Returns public IP and SSH command

### API Gateway
- HTTP API with POST and OPTIONS routes
- Forwards requests to Lambda using AWS_PROXY integration

### Terraform
- Provisions Lambda, API Gateway, IAM roles
- Auto-deploys changes with `$default` stage


### Jenkins
- Automates API calls using `lambda_api_runner.py`
- Can be triggered manually or on GitHub push

---

## ⚙️ Setup Instructions

### 1. Deploy Infrastructure with Terraform
```bash
cd terraform
terraform init
terraform apply
```

### 2. Package Lambda Function
```bash
zip lambda.zip lambda_handler.py
```


## 🔐 IAM Permissions

Attach these to Lambda role:
```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:*",
    "secretsmanager:*"
  ],
  "Resource": "*"
}
```
Also attach: `AWSLambdaBasicExecutionRole`

---

## 🧰 Jenkins Pipeline Configuration

### Sample Jenkinsfile

pipeline {
  agent any
  environment {
    ENDPOINT = 'https://<your-api-id>.execute-api.us-east-1.amazonaws.com'
    MY_IP = '136.226.232.163/32'
  }
  stages {
    stage('Run Lambda API') {
      steps {
        bat 'python lambda_api_runner.py'
      }
    }
  }
}

