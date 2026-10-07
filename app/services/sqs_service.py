"""
AWS SQS Service - Asynchronous message processing.
Handles inventory updates, order processing, and notifications via Amazon SQS.
"""

import json
import logging
import boto3
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)

class SQSService:
    """AWS SQS operations service."""

    _instance = None
    _client = None
    _queue_urls = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self):
        """Lazily initialize SQS Client."""
        if self._client is None:
            try:
                region = current_app.config.get('AWS_REGION', 'ap-south-1')
                self._client = boto3.client('sqs', region_name=region)
                logger.info('SQS client initialized.')
            except Exception as e:
                logger.error(f'Failed to initialize SQS: {e}')
                return None
        return self._client

    def _get_or_create_queue(self, queue_name: str) -> str:
        """Ensure a queue exists and return its URL."""
        if queue_name in self._queue_urls:
            return self._queue_urls[queue_name]

        client = self._get_client()
        if client is None:
            return None

        try:
            # Try to get the queue URL
            response = client.get_queue_url(QueueName=queue_name)
            self._queue_urls[queue_name] = response['QueueUrl']
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                # Queue doesn't exist, create it
                try:
                    logger.info(f'Creating SQS queue: {queue_name}')
                    response = client.create_queue(QueueName=queue_name)
                    self._queue_urls[queue_name] = response['QueueUrl']
                except Exception as create_err:
                    logger.error(f'Error creating queue {queue_name}: {create_err}')
                    return None
            else:
                logger.error(f'Error accessing queue {queue_name}: {e}')
                return None

        return self._queue_urls.get(queue_name)

    def send_message(self, queue_name: str, message_dict: dict) -> bool:
        """Serialize a dict to JSON and send to the queue."""
        try:
            client = self._get_client()
            queue_url = self._get_or_create_queue(queue_name)
            if not client or not queue_url:
                logger.warning(f'Queue {queue_name} unavailable. Message not sent.')
                return False
                
            message_str = json.dumps(message_dict)
            client.send_message(
                QueueUrl=queue_url,
                MessageBody=message_str
            )
            logger.info(f'Message sent to queue {queue_name}.')
            return True
        except Exception as e:
            logger.error(f'Error sending message to {queue_name}: {e}')
            return False

    def receive_messages(self, queue_name: str, max_messages: int = 5,
                         visibility_timeout: int = 30) -> list:
        """Receive and deserialize messages from the queue."""
        try:
            client = self._get_client()
            queue_url = self._get_or_create_queue(queue_name)
            if not client or not queue_url:
                return []
                
            # SQS MaxNumberOfMessages max is 10
            max_msgs = min(10, max_messages)
            
            response = client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_msgs,
                VisibilityTimeout=visibility_timeout,
                WaitTimeSeconds=0 # Short polling
            )
            
            messages = response.get('Messages', [])
            result = []
            for msg in messages:
                try:
                    data = json.loads(msg['Body'])
                except (json.JSONDecodeError, Exception):
                    data = msg['Body']
                
                result.append({
                    'id': msg['MessageId'],
                    'pop_receipt': msg['ReceiptHandle'],
                    'data': data
                })
            return result
        except Exception as e:
            logger.error(f'Error receiving messages from {queue_name}: {e}')
            return []

    def delete_message(self, queue_name: str, message_id: str, pop_receipt: str):
        """Delete a processed message from the queue."""
        try:
            client = self._get_client()
            queue_url = self._get_or_create_queue(queue_name)
            if client and queue_url:
                client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=pop_receipt
                )
        except Exception as e:
            logger.error(f'Error deleting message from {queue_name}: {e}')

    def get_queue_length(self, queue_name: str) -> int:
        """Get approximate message count in a queue."""
        try:
            client = self._get_client()
            queue_url = self._get_or_create_queue(queue_name)
            if not client or not queue_url:
                return 0
                
            response = client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages']
            )
            return int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
        except Exception as e:
            logger.error(f'Error getting queue length for {queue_name}: {e}')
            return 0

    # --- Convenience Methods for Application Queues ---

    def send_inventory_update(self, product_id: str, warehouse_id: str,
                              quantity_change: int, movement_type: str,
                              reference_id: str = '', user_id: str = '') -> bool:
        """Send an inventory update message to the inventory-updates queue."""
        queue_name = current_app.config.get('AZURE_QUEUE_INVENTORY_UPDATES', 'inventory-updates')
        return self.send_message(queue_name, {
            'type': 'inventory_update',
            'product_id': product_id,
            'warehouse_id': warehouse_id,
            'quantity_change': quantity_change,
            'movement_type': movement_type,
            'reference_id': reference_id,
            'user_id': user_id
        })

    def send_order_processing(self, order_id: str, order_type: str,
                              action: str, user_id: str = '') -> bool:
        """Send an order processing message."""
        queue_name = current_app.config.get('AZURE_QUEUE_ORDER_PROCESSING', 'order-processing')
        return self.send_message(queue_name, {
            'type': 'order_processing',
            'order_id': order_id,
            'order_type': order_type,
            'action': action,
            'user_id': user_id
        })

    def send_notification(self, user_id: str, notification_type: str,
                          title: str, message: str,
                          severity: str = 'info', action_url: str = '') -> bool:
        """Send a notification message."""
        queue_name = current_app.config.get('AZURE_QUEUE_NOTIFICATIONS', 'notifications')
        return self.send_message(queue_name, {
            'type': 'notification',
            'user_id': user_id,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'severity': severity,
            'action_url': action_url
        })


# Singleton instance exported with the old name for backward compatibility
sqs_service = SQSService()
