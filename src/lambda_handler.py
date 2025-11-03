# import json
# import boto3
# import os
# import time
# import uuid
# from botocore.exceptions import ClientError

# ec2 = boto3.client('ec2')
# secrets = boto3.client('secretsmanager')

# def lambda_handler(event, context):
#     print("Received event:", event)

#     try:
#         body = json.loads(event.get("body", "{}"))
#     except Exception:
#         return response(400, {'error': 'Invalid JSON in request body'})

#     action = body.get('action')
#     instance_id = body.get('instance_id')
#     name = body.get('name', 'ec2-instance')
#     ami_id = os.getenv('AMI_ID', 'ami-08982f1c5bf93d976')
#     instance_type = 't3.micro'

#     if not action:
#         return response(400, {'error': 'Action is required'})

#     key_name = f"{name}-key-{str(uuid.uuid4())[:8]}"
#     sg_name = f"{name}-ssh-sg"

#     try:
#         if action == 'create':
#             # Create Key Pair and store in Secrets Manager
#             try:
#                 key_pair = ec2.create_key_pair(KeyName=key_name)
#                 private_key = key_pair['KeyMaterial']
#                 secrets.create_secret(Name=key_name, SecretString=private_key)
#             except ClientError as e:
#                 if 'InvalidKeyPair.Duplicate' in str(e):
#                     return response(400, {'error': f"Key '{key_name}' already exists"})
#                 else:
#                     return response(500, {'error': f"Key creation error: {str(e)}"})

#             # Create Security Group
#             try:
#                 sg_result = ec2.create_security_group(
#                     GroupName=sg_name,
#                     Description='Allow SSH access',
#                     VpcId=get_default_vpc_id()
#                 )
#                 sg_id = sg_result['GroupId']
#                 ec2.authorize_security_group_ingress(
#                     GroupId=sg_id,
#                     IpPermissions=[{
#                         'IpProtocol': 'tcp',
#                         'FromPort': 22,
#                         'ToPort': 22,
#                         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
#                     }]
#                 )
#             except ClientError as e:
#                 if 'InvalidGroup.Duplicate' in str(e):
#                     sg_id = get_security_group_id(sg_name)
#                 else:
#                     return response(500, {'error': f"Security group error: {str(e)}"})

#             # Launch EC2 Instance
#             try:
#                 new_instance = ec2.run_instances(
#                     ImageId=ami_id,
#                     InstanceType=instance_type,
#                     MinCount=1,
#                     MaxCount=1,
#                     KeyName=key_name,
#                     SecurityGroupIds=[sg_id]
#                 )
#                 instance = new_instance['Instances'][0]
#                 instance_id = instance['InstanceId']

#                 waiter = ec2.get_waiter('instance_running')
#                 waiter.wait(InstanceIds=[instance_id])

#                 desc = ec2.describe_instances(InstanceIds=[instance_id])
#                 public_ip = desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')
#             except Exception as e:
#                 return response(500, {'error': f"EC2 launch error: {str(e)}"})

#             ssh_command = f"ssh -i <downloaded-key>.pem ec2-user@{public_ip}"

#             return response(200, {
#                 'message': f'Created instance {instance_id}',
#                 'data': {
#                     'instance_id': instance_id,
#                     'public_ip': public_ip,
#                     'ssh_command': ssh_command,
#                     'ssh_key_secret': key_name
#                 }
#             })

#         elif action == 'start':
#             if not instance_id:
#                 return response(400, {'error': 'Missing "instance_id" for start'})
#             ec2.start_instances(InstanceIds=[instance_id])
#             return response(200, {'message': f'Started instance {instance_id}'})

#         elif action == 'stop':
#             if not instance_id:
#                 return response(400, {'error': 'Missing "instance_id" for stop'})
#             ec2.stop_instances(InstanceIds=[instance_id])
#             return response(200, {'message': f'Stopped instance {instance_id}'})

#         elif action == 'terminate':
#             if not instance_id:
#                 return response(400, {'error': 'Missing "instance_id" for terminate'})

#             desc = ec2.describe_instances(InstanceIds=[instance_id])
#             instance = desc['Reservations'][0]['Instances'][0]
#             sg_id = instance['SecurityGroups'][0]['GroupId']

#             ec2.terminate_instances(InstanceIds=[instance_id])
#             while True:
#                 check_result = ec2.describe_instances(InstanceIds=[instance_id])
#                 state = check_result['Reservations'][0]['Instances'][0]['State']['Name']
#                 if state == 'terminated':
#                     break
#                 time.sleep(5)
            
#             # Add a delay here to allow AWS to release the SG from ENIs
#             time.sleep(15)

#             secrets.delete_secret(SecretId=key_name, ForceDeleteWithoutRecovery=True)
#             ec2.delete_key_pair(KeyName=key_name)
#             ec2.delete_security_group(GroupId=sg_id)

#             return response(200, {'message': f'Instance {instance_id} terminated and resources cleaned up'})

#         elif action == 'list':
#             list_result = ec2.describe_instances()
#             instances = []
#             for reservation in list_result['Reservations']:
#                 for instance in reservation['Instances']:
#                     instances.append({
#                         'instance_id': instance['InstanceId'],
#                         'state': instance['State']['Name'],
#                         'public_ip': instance.get('PublicIpAddress', 'None'),
#                         'instance_type': instance['InstanceType']
#                     })
#             return response(200, {'message': f'Found {len(instances)} instances', 'data': instances})

#         else:
#             return response(400, {'error': 'Invalid action. Use create, start, stop, terminate, or list.'})

#     except Exception as e:
#         return response(500, {'error': f'Unexpected error: {str(e)}'})


# def get_default_vpc_id():
#     vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
#     return vpcs['Vpcs'][0]['VpcId']

# def get_security_group_id(group_name):
#     sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [group_name]}])
#     return sgs['SecurityGroups'][0]['GroupId']

# def response(status, message):
#     return {
#         'statusCode': status,
#         'headers': {
#             'Content-Type': 'application/json',
#             'Access-Control-Allow-Origin': '*',
#             'Access-Control-Allow-Methods': 'POST, OPTIONS',
#             'Access-Control-Allow-Headers': 'Content-Type, Authorization',
#         },
#         'body': json.dumps(message)
#     } 

import json
import boto3
import os
import time
import uuid
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')
secrets = boto3.client('secretsmanager')

def lambda_handler(event, context):
    print("Received event:", event)

    try:
        body = json.loads(event.get("body", "{}"))
    except Exception:
        return response(400, {'error': 'Invalid JSON in request body'})

    action = body.get('action')
    instance_id = body.get('instance_id')
    name = body.get('name', 'ec2-instance')
    ami_id = os.getenv('AMI_ID', 'ami-08982f1c5bf93d976')
    instance_type = 't3.micro'

    if not action:
        return response(400, {'error': 'Action is required'})

    key_name = f"{name}-key-{str(uuid.uuid4())[:8]}"
    sg_name = f"{name}-ssh-sg"

    try:
        if action == 'create':
            # Create Key Pair and store in Secrets Manager
            try:
                key_pair = ec2.create_key_pair(KeyName=key_name)
                private_key = key_pair['KeyMaterial']
                secrets.create_secret(Name=key_name, SecretString=private_key)
            except ClientError as e:
                if 'InvalidKeyPair.Duplicate' in str(e):
                    return response(400, {'error': f"Key '{key_name}' already exists"})
                else:
                    return response(500, {'error': f"Key creation error: {str(e)}"})

            # Create Security Group
            try:
                sg_result = ec2.create_security_group(
                    GroupName=sg_name,
                    Description='Allow SSH access',
                    VpcId=get_default_vpc_id()
                )
                sg_id = sg_result['GroupId']
                ec2.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=[{
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }]
                )
            except ClientError as e:
                if 'InvalidGroup.Duplicate' in str(e):
                    sg_id = get_security_group_id(sg_name)
                else:
                    return response(500, {'error': f"Security group error: {str(e)}"})

            # Launch EC2 Instance
            try:
                instance = ec2.run_instances(
                    ImageId=ami_id,
                    InstanceType=instance_type,
                    MinCount=1,
                    MaxCount=1,
                    KeyName=key_name,
                    SecurityGroupIds=[sg_id]
                )
                instance = instance['Instances'][0]
                instance_id = instance['InstanceId']

                waiter = ec2.get_waiter('instance_running')
                waiter.wait(InstanceIds=[instance_id])

                desc = ec2.describe_instances(InstanceIds=[instance_id])
                public_ip = desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')
            except Exception as e:
                return response(500, {'error': f"EC2 launch error: {str(e)}"})

            ssh_command = f"ssh -i <downloaded-key>.pem ec2-user@{public_ip}"

            return response(200, {
                'message': f'Created instance {instance_id}',
                'data': {
                    'instance_id': instance_id,
                    'public_ip': public_ip,
                    'ssh_command': ssh_command,
                    'ssh_key_secret': key_name
                }
            })

        elif action == 'start':
            if not instance_id:
                return response(400, {'error': 'Missing "instance_id" for start'})
            ec2.start_instances(InstanceIds=[instance_id])
            return response(200, {'message': f'Started instance {instance_id}'})

        elif action == 'stop':
            if not instance_id:
                return response(400, {'error': 'Missing "instance_id" for stop'})
            ec2.stop_instances(InstanceIds=[instance_id])
            return response(200, {'message': f'Stopped instance {instance_id}'})

        elif action == 'terminate':
            if not instance_id:
                return response(400, {'error': 'Missing "instance_id" for terminate'})

            # Describe instance to get SG
            desc = ec2.describe_instances(InstanceIds=[instance_id])
            instance = desc['Reservations'][0]['Instances'][0]
            sg_id = instance['SecurityGroups'][0]['GroupId']

            # Terminate instance
            ec2.terminate_instances(InstanceIds=[instance_id])

            # Wait for termination (max 20 sec)
            waiter = ec2.get_waiter('instance_terminated')
            try:
                waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 5, 'MaxAttempts': 4})
            except:
                pass  # Don't block too long

            # Attempt cleanup without blocking API Gateway
            cleanup_resources(key_name, sg_id)

            return response(200, {
                'message': f'Termination initiated for {instance_id}. Cleanup attempted.'
            })

        elif action == 'list':
            list_result = ec2.describe_instances()
            instances = []
            for reservation in list_result['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'instance_id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'public_ip': instance.get('PublicIpAddress', 'None'),
                        'instance_type': instance['InstanceType']
                    })
            return response(200, {'message': f'Found {len(instances)} instances', 'data': instances})

        else:
            return response(400, {'error': 'Invalid action. Use create, start, stop, terminate, or list.'})

    except Exception as e:
        return response(500, {'error': f'Unexpected error: {str(e)}'})


def cleanup_resources(key_name, sg_id):
    try:
        # Delete secret
        secrets.delete_secret(SecretId=key_name, ForceDeleteWithoutRecovery=True)
    except Exception as e:
        print(f"Secret cleanup skipped: {e}")

    try:
        # Delete key pair
        ec2.delete_key_pair(KeyName=key_name)
    except Exception as e:
        print(f"Key pair cleanup skipped: {e}")

    try:
        # Delete SG only if no ENIs attached
        enis = ec2.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg_id]}])
        if not enis['NetworkInterfaces']:
            ec2.delete_security_group(GroupId=sg_id)
        else:
            print(f"SG {sg_id} still attached, skipping deletion.")
    except Exception as e:
        print(f"SG cleanup skipped: {e}")


def get_default_vpc_id():
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    return vpcs['Vpcs'][0]['VpcId']

def get_security_group_id(group_name):
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': [group_name]}])
    return sgs['SecurityGroups'][0]['GroupId']

def response(status, message):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
        'body': json.dumps(message)
    }
