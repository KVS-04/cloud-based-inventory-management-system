"""
AWS S3 Service - File storage integration.
Handles product images, reports, and archived data using Amazon S3.
"""

import logging
import uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta
from flask import current_app

logger = logging.getLogger(__name__)

class S3Service:
    """AWS S3 operations service."""

    _instance = None
    _client = None
    _bucket_name = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self):
        """Lazily initialize S3 client."""
        if self._client is None:
            try:
                region = current_app.config.get('AWS_REGION', 'ap-south-1')
                self._client = boto3.client('s3', region_name=region)
                logger.info('S3 client initialized.')
            except Exception as e:
                logger.error(f'Failed to initialize S3: {e}')
                return None
        return self._client

    def _get_bucket_name(self):
        """Get or create the single globally unique S3 bucket for this app."""
        if self._bucket_name is None:
            client = self._get_client()
            if client is None:
                return None
            
            # Since S3 bucket names must be globally unique, we'll try to use a predefined one
            # from config, or generate one and ensure it exists.
            region = current_app.config.get('AWS_REGION', 'ap-south-1')
            
            # Use account ID to make a unique bucket name
            try:
                sts = boto3.client('sts', region_name=region)
                account_id = sts.get_caller_identity()['Account']
                self._bucket_name = f"inventory-app-storage-{account_id}-{region}"
            except Exception:
                # Fallback if sts fails
                self._bucket_name = f"inventory-app-storage-demo-{uuid.uuid4().hex[:8]}"

            try:
                client.head_bucket(Bucket=self._bucket_name)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    # Bucket does not exist, create it
                    logger.info(f'Creating S3 bucket: {self._bucket_name}')
                    try:
                        if region == 'us-east-1':
                            client.create_bucket(Bucket=self._bucket_name)
                        else:
                            client.create_bucket(
                                Bucket=self._bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': region}
                            )
                    except Exception as create_err:
                        logger.error(f'Failed to create S3 bucket: {create_err}')
                        return None
                else:
                    logger.error(f'Error checking bucket {self._bucket_name}: {e}')
                    return None

        return self._bucket_name

    def _get_s3_key(self, container_name: str, filename: str) -> str:
        """Map Azure container concepts to S3 prefixes (folders)."""
        return f"{container_name}/{filename}".strip('/')

    def upload_file(self, container_name: str, file, filename: str) -> str:
        """Upload a file object to S3. Returns the public-facing URL."""
        try:
            client = self._get_client()
            bucket = self._get_bucket_name()
            if not client or not bucket:
                raise ConnectionError('S3 unavailable.')
            
            s3_key = self._get_s3_key(container_name, filename)
            
            # Get content type
            content_type = getattr(file, 'content_type', 'application/octet-stream')
            
            client.upload_fileobj(
                file, bucket, s3_key,
                ExtraArgs={'ContentType': content_type}
            )
            return self.get_file_url(container_name, filename)
        except Exception as e:
            logger.error(f'Error uploading file {filename}: {e}')
            raise

    def upload_bytes(self, container_name: str, data: bytes,
                     filename: str, content_type: str = 'application/octet-stream') -> str:
        """Upload bytes data to S3."""
        try:
            client = self._get_client()
            bucket = self._get_bucket_name()
            if not client or not bucket:
                raise ConnectionError('S3 unavailable.')
                
            s3_key = self._get_s3_key(container_name, filename)
            
            client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=data,
                ContentType=content_type
            )
            return self.get_file_url(container_name, filename)
        except Exception as e:
            logger.error(f'Error uploading bytes {filename}: {e}')
            raise

    def download_file(self, container_name: str, filename: str) -> bytes:
        """Download a file from S3 as bytes."""
        try:
            client = self._get_client()
            bucket = self._get_bucket_name()
            if not client or not bucket:
                return None
                
            s3_key = self._get_s3_key(container_name, filename)
            response = client.get_object(Bucket=bucket, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f'Error downloading {filename}: {e}')
            return None

    def get_file_url(self, container_name: str, filename: str) -> str:
        """Get the public URL for an S3 object."""
        try:
            region = current_app.config.get('AWS_REGION', 'ap-south-1')
            bucket = self._get_bucket_name()
            s3_key = self._get_s3_key(container_name, filename)
            return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        except Exception as e:
            logger.error(f'Error getting URL for {filename}: {e}')
            return ''

    def delete_file(self, container_name: str, filename: str):
        """Delete an object from S3."""
        try:
            client = self._get_client()
            bucket = self._get_bucket_name()
            if not client or not bucket:
                return
                
            s3_key = self._get_s3_key(container_name, filename)
            client.delete_object(Bucket=bucket, Key=s3_key)
            logger.info(f'Deleted {s3_key} from {bucket}.')
        except Exception as e:
            logger.error(f'Error deleting {filename}: {e}')

    def list_files(self, container_name: str, prefix: str = '') -> list:
        """List objects in an S3 'container' (prefix)."""
        try:
            client = self._get_client()
            bucket = self._get_bucket_name()
            if not client or not bucket:
                return []
                
            s3_prefix = self._get_s3_key(container_name, prefix)
            response = client.list_objects_v2(Bucket=bucket, Prefix=s3_prefix)
            
            result = []
            for obj in response.get('Contents', []):
                # Remove the container_name/ part to emulate Azure API
                name = obj['Key'][len(container_name)+1:] if obj['Key'].startswith(f"{container_name}/") else obj['Key']
                result.append({
                    'name': name,
                    'size': obj['Size'],
                    'last_modified': str(obj['LastModified'])
                })
            return result
        except Exception as e:
            logger.error(f'Error listing files in {container_name}: {e}')
            return []

    def generate_sas_url(self, container_name: str, filename: str,
                         expiry_hours: int = 1) -> str:
        """Generate a Presigned URL for temporary access (equivalent to Azure SAS)."""
        try:
            client = self._get_client()
            bucket = self._get_bucket_name()
            if not client or not bucket:
                return ''
                
            s3_key = self._get_s3_key(container_name, filename)
            
            url = client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': s3_key},
                ExpiresIn=expiry_hours * 3600
            )
            return url
        except Exception as e:
            logger.error(f'Error generating presigned URL: {e}')
            return ''

    def upload_product_image(self, file, product_id: str) -> str:
        """Upload a product image to the product-images prefix."""
        container = current_app.config.get('AZURE_BLOB_CONTAINER_IMAGES', 'product-images')
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
        filename = f"products/{product_id}/{uuid.uuid4().hex}.{ext}"
        return self.upload_file(container, file, filename)

    def upload_report(self, data: bytes, filename: str, content_type: str) -> str:
        """Upload a generated report to the reports prefix."""
        container = current_app.config.get('AZURE_BLOB_CONTAINER_REPORTS', 'reports')
        return self.upload_bytes(container, data, filename, content_type)


# Singleton instance exported with the old name for backward compatibility
s3_storage = S3Service()
