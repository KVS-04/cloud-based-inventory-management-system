import boto3
import json
from app import create_app
from app.services.s3_service import s3_storage

app = create_app()
with app.app_context():
    bucket_name = s3_storage._get_bucket_name()
    print(f"Bucket name: {bucket_name}")
    
    s3_client = s3_storage._get_client()
    
    # 1. Delete the Public Access Block
    print("Removing Block Public Access...")
    try:
        s3_client.delete_public_access_block(Bucket=bucket_name)
    except Exception as e:
        print(f"Error deleting block: {e}")
        
    # 2. Add a bucket policy to allow public read
    print("Applying Public Read Policy...")
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            }
        ]
    }
    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
        print("Success! Bucket is now public.")
    except Exception as e:
        print(f"Error applying policy: {e}")
