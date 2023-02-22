import boto3
import json

ec2 = boto3.resource('ec2',region_name='ap-south-1')

vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
vpc.create_tags(Tags=[{"Key": "Name", "Value": "MyVPC"}])
vpc.wait_until_available()

subnet = ec2.create_subnet(CidrBlock='10.0.0.0/24', VpcId=vpc.id)
subnet.create_tags(Tags=[{"Key": "Name", "Value": "MySubnet"}])

instance = ec2.create_instances(
    ImageId='ami-0e742cca61fb65051',
    InstanceType='t2.micro',
    MaxCount=1,
    MinCount=1,
    KeyName='KeyPair1',
    NetworkInterfaces=[{
        'SubnetId': subnet.id,
        'DeviceIndex': 0,
        'AssociatePublicIpAddress': True,
        
    }],
    UserData='''#!/bin/bash
                sudo apt update
                sudo apt install nginx -y
                sudo systemctl start nginx
                '''
)
instance[0].wait_until_running()

s3 = boto3.resource('s3')
bucket_name = 'my-commvault-bucket'
bucket = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
    'LocationConstraint': 'ap-south-1'
})



bucket.Website().put(
    WebsiteConfiguration={
        'IndexDocument': {'Suffix': 'index.html'}
    }
)
s3_client = boto3.client('s3')

bucket_name = 'my-commvault-bucket'

bucket_policy = {
    'Version': '2012-10-17',
    'Statement': [{
        'Sid': 'AddPerm',
        'Effect': 'Allow',
        'Principal': '*',
        'Action': ['s3:GetObject'],
        'Resource': "arn:aws:s3:::%s/*" % bucket_name
    }]
}


bucket_policy = json.dumps(bucket_policy)

s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
s3_client.upload_file(
    Filename='index.html',
    Bucket=bucket_name,
    Key='index.html',
    ExtraArgs={
        'ContentType': 'text/html'
    }
)