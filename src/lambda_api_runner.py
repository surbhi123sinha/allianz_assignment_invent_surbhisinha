import requests
import json
import os
 
# Your API endpoint (from Terraform outputs—update if changed)
ENDPOINT = os.getenv('ENDPOINT', 'https://11fb1wqzn4.execute-api.us-east-1.amazonaws.com')
 
# Your public IP for security (from whatismyip.com + /32—update with yours)
# MY_IP = os.getenv('MY_IP', '165.225.120.94/32')  
MY_IP = os.getenv('MY_IP', '136.226.232.163/32') 
 
def call_api(action, instance_id=None):
    payload = {'action': action}
    if instance_id:
        payload['instance_id'] = instance_id
   
    # For create: Add IP restriction (your Lambda can use this to update SG inbound)
    if action == 'create':
        payload['allowed_cidr'] = MY_IP  # Uses your IP for SSH access
   
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f"{ENDPOINT}/", json=payload, headers=headers)
   
    try:
        data = response.json()
        if 'body' in data:
            body = json.loads(data['body'])
            print(f"API Response: {body}")
            return body
        else:
            print(f"Direct Response: {data}")
            return data
    except:
        print(f"Error: {response.text}")
        return None
 
if __name__ == '__main__':
    # Default action: 'create' (change to 'list', 'stop', etc., or set ACTION env var in Jenkins)
    action = os.getenv('ACTION', 'create')  # Examples: 'stop', 'list', 'terminate'
    instance_id = os.getenv('INSTANCE_ID')  # Optional, e.g., 'i-02faf7724931b5c0c' for stop/terminate
    result = call_api(action, instance_id)
    if result and 'error' not in str(result).lower():
        # print("Success! Check EC2 console for details.")
        print("EC2 action completed successfully!")
    else:
        print("Failed—check AWS Lambda logs or response above.")
 