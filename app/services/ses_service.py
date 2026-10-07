"""
AWS SES Service - Email delivery.
Handles sending transactional emails like alerts and reports via Amazon SES.
"""

import logging
import boto3
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)

class SESService:
    """AWS Simple Email Service operations."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self):
        """Lazily initialize SES client."""
        if self._client is None:
            try:
                region = current_app.config.get('AWS_REGION', 'ap-south-1')
                self._client = boto3.client('ses', region_name=region)
                logger.info('SES client initialized.')
            except Exception as e:
                logger.error(f'Failed to initialize SES: {e}')
                return None
        return self._client

    def send_email(self, to_addresses: list, subject: str, 
                   body_text: str, body_html: str = None, 
                   sender_email: str = None) -> bool:
        """Send an email using Amazon SES."""
        client = self._get_client()
        if not client:
            return False

        # In a real app, this should be verified in AWS SES Console
        sender = sender_email or current_app.config.get('ADMIN_EMAIL', 'admin@inventory.com')
        
        # Ensure it's a list
        if isinstance(to_addresses, str):
            to_addresses = [to_addresses]

        message = {
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body_text,
                    'Charset': 'UTF-8'
                }
            }
        }

        if body_html:
            message['Body']['Html'] = {
                'Data': body_html,
                'Charset': 'UTF-8'
            }

        try:
            response = client.send_email(
                Source=sender,
                Destination={
                    'ToAddresses': to_addresses
                },
                Message=message
            )
            logger.info(f"Email sent! Message ID: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"Error sending email: {e.response['Error']['Message']}")
            return False

# Singleton instance
ses_service = SESService()
