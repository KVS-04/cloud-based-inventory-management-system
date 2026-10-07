import json
import logging
import boto3
import os
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients outside the handler so they are reused across Lambda invocations
REGION = os.environ.get('AWS_REGION', 'ap-south-1')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'admin@inventory.com')

ses_client = boto3.client('ses', region_name=REGION)
dynamodb_resource = boto3.resource('dynamodb', region_name=REGION)

def lambda_handler(event, context):
    """
    Main AWS Lambda Handler triggered by Amazon SQS.
    Processes messages for notifications, inventory updates, and order processing.
    """
    logger.info(f"Received {len(event['Records'])} records from SQS.")
    
    for record in event['Records']:
        try:
            # SQS payload is stored in the 'body' attribute
            body = json.loads(record['body'])
            message_type = body.get('type')

            logger.info(f"Processing message type: {message_type}")
            
            if message_type == 'notification':
                process_notification(body)
            elif message_type == 'inventory_update':
                process_inventory_update(body)
            elif message_type == 'order_processing':
                process_order(body)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error processing record {record.get('messageId')}: {e}")
            # If we raise an exception, SQS will retry the message later.
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed SQS messages.')
    }


def process_notification(data):
    """Handles sending an email via Amazon SES."""
    user_id = data.get('user_id')
    title = data.get('title', 'Notification from Inventory App')
    message = data.get('message', '')
    
    # In a real app, we would query DynamoDB to get the user's email by user_id
    # For this Lambda, we'll assume the email is passed, or we look it up
    
    email_to = data.get('email')
    
    if not email_to:
        # Fallback DynamoDB lookup
        try:
            users_table = dynamodb_resource.Table('users')
            response = users_table.get_item(Key={'id': user_id})
            user = response.get('Item')
            if user:
                email_to = user.get('email')
        except Exception as e:
            logger.error(f"Could not fetch user email from DynamoDB: {e}")
            return
            
    if not email_to:
        logger.error(f"No email address found for user {user_id}. Cannot send email.")
        return

    # Send the email via SES
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [email_to]},
            Message={
                'Subject': {'Data': title, 'Charset': 'UTF-8'},
                'Body': {'Text': {'Data': message, 'Charset': 'UTF-8'}}
            }
        )
        logger.info(f"SES Email sent successfully! MessageId: {response['MessageId']}")
    except ClientError as e:
        logger.error(f"SES Error: {e.response['Error']['Message']}")
        raise e


def process_inventory_update(data):
    """Handles asynchronous inventory math/updates in DynamoDB."""
    product_id = data.get('product_id')
    qty_change = data.get('quantity_change', 0)
    
    logger.info(f"Updating inventory for Product {product_id}. Change: {qty_change}")
    # Additional DynamoDB updates would go here.


def process_order(data):
    """Handles asynchronous order status updates."""
    order_id = data.get('order_id')
    action = data.get('action')
    
    logger.info(f"Processing Order {order_id} - Action: {action}")
    # Additional DynamoDB updates would go here.

