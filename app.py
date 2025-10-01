from flask import Flask, render_template_string, request
import requests
import json
from requests_aws4auth import AWS4Auth
import boto3

app = Flask(__name__)




API_URL = "https://6xzeq28mbi.execute-api.us-east-1.amazonaws.com/stg"

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AWS Instance Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
</head>
<body style="background-color: #e6ffe6;">
<div class="container py-5">
<div class="row justify-content-center">
<div class="col-md-9">
<div class="card shadow-lg" style="background-color: #FFE4E1;">
<div class="card-header bg-primary text-white text-center">
<h3><i class="bi bi-hdd-network"></i> AWS Instance Dashboard </h3>
</div>
<div class="card-body">
<form method="post" action="/ec2" class="d-flex justify-content-center gap-3 mb-4">
<div class="row" style="display: flex; align-items: flex-start;">
    <!-- Dropdown Section -->
    <div class="col-md-9 p-4 mb-3 rounded" style="background-color: #e0f7fa; margin-right: 0px;">
        <label for="instance_id" class="form-label fw-bold" style="color: #00796b;">Select EC2 Instance</label>
        <select id="instance_id" name="instance_id" class="form-select" style="width: 100%; font-size: 1rem;">
            <option value="" disabled selected>Select an instance</option>
            {% for inst in instances %}
                <option value="{{ inst['InstanceId'] }}">
                    {{ inst['InstanceId'] }} - {{ inst['State'] }} - {{ inst['PublicIpAddress'] or 'No Public IP' }}
                </option>
            {% endfor %}
        </select>
    </div>

    <!-- Button Section -->
    <div class="col-md-3 p-4 mb-3 rounded" style="background-color: #fff8dc;">
        <div class="d-flex flex-column gap-2">
            <button type="submit" name="action" value="create" class="btn btn-info text-nowrap">
                <i class="bi bi-plus-circle"></i> Create
            </button>
            <button type="submit" name="action" value="start" class="btn btn-success text-nowrap">
                <i class="bi bi-play-circle"></i> Start
            </button>
            <button type="submit" name="action" value="stop" class="btn btn-danger text-nowrap">
                <i class="bi bi-stop-circle"></i> Stop
            </button>
            <button type="submit" name="action" value="terminate" class="btn btn-warning text-nowrap">
                <i class="bi bi-x-circle"></i> Terminate
            </button>
        </div>
    </div>
</div>

</form>

<br>                       
{% if success %}
<div class="alert alert-success text-center">
    <i class="bi bi-check-circle"></i> {{ success|safe }}
</div>
{% endif %}

 
                        {% if result %}
<div class="alert alert-info">
<strong>Result:</strong> {{ result }}
</div>
 
                        {% endif %}
</div>
 
</div>
</div>
</div>
</div>
</body>
</html>
 
"""

ec2 = boto3.client('ec2', region_name='us-east-1')  
def fetch_all_instances():
    instances = []
    try:
        response = ec2.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'State': instance['State']['Name'],
                    'PublicIpAddress': instance.get('PublicIpAddress')
                })
    except Exception as e:
        print(f"Error fetching instances: {e}")
    return instances 

@app.route("/ec2", methods=["GET", "POST"])
def ec2_control():
    result = None
    instances = fetch_all_instances()

    if request.method == "POST":
        action = request.form.get("action")
        instance_id = request.form.get("instance_id")

        if action == "create":
            payload = {"action": action}
        else:
            if not instance_id:
                result = "Please select an instance."
                return render_template_string(HTML, result=result, success=None, instances=instances)
            payload = {"action": action, "instance_id": instance_id}

        try:
            # Get AWS credentials
            session = boto3.Session()
            credentials = session.get_credentials()
            region = "us-east-1"

            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                region,
                "execute-api",
                session_token=credentials.token
            )

            # Make signed request
            response = requests.post(API_URL, json=payload, auth=awsauth)
            
            data = response.json()
            body = json.loads(data["body"]) if "body" in data else data
            result = body  
        except Exception as e:
            result = f"Error parsing response: {str(e)}"

    return render_template_string(HTML, result=result, success=None, instances=instances)

if __name__ == "__main__":
    app.run(debug=True) 
