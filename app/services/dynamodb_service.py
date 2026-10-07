"""
AWS DynamoDB Service - Primary database integration.
Handles all CRUD operations against Amazon DynamoDB.
"""

import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from flask import current_app
import re

logger = logging.getLogger(__name__)

# Container definitions map to DynamoDB tables and their partition keys
CONTAINER_CONFIGS = {
    'users': 'role',
    'products': 'category',
    'inventory': 'warehouse_id',
    'inventory_movements': 'product_id',
    'purchase_orders': 'status',
    'sales_orders': 'status',
    'returns': 'return_type',
    'suppliers': 'category',
    'warehouses': 'region',
    'notifications': 'user_id',
    'audit_logs': 'entity_type',
}

class DynamoDBService:
    """AWS DynamoDB operations service."""

    _instance = None
    _resource = None
    _client = None
    _tables = {}

    def __new__(cls):
        """Singleton pattern to reuse the DynamoDB client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_resource(self):
        """Lazily initialize the DynamoDB resource."""
        if self._resource is None:
            try:
                region = current_app.config.get('AWS_REGION', 'ap-south-1')
                self._resource = boto3.resource('dynamodb', region_name=region)
                self._client = boto3.client('dynamodb', region_name=region)
                logger.info('DynamoDB resource initialized successfully.')
            except Exception as e:
                logger.error(f'Failed to initialize DynamoDB: {e}')
                return None
        return self._resource

    def get_container(self, container_name: str):
        """Get or create a table with the appropriate partition key.
        Note: DynamoDB table creation is asynchronous, but we wait for it.
        We will use a composite key for everything to match the Cosmos DB pattern:
        Partition Key = 'pk' (which maps to the old partition key)
        Sort Key = 'id'
        Wait, cosmos used 'id' as the document id, and partition_key as the partition.
        To keep it simple, let's just use 'id' as Partition Key for DynamoDB since every item has a unique ID, 
        and we don't do complex querying on the Cosmos partition key most of the time.
        Actually, we can just use 'id' as the HASH key for all tables.
        """
        if container_name not in self._tables:
            resource = self._get_resource()
            if resource is None:
                return None
            try:
                # Try to get table, if not exists, create it
                table = resource.Table(container_name)
                table.load() # This will throw ClientError if table doesn't exist
                self._tables[container_name] = table
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    try:
                        # Create table with 'id' as partition key
                        logger.info(f'Creating table {container_name}...')
                        table = resource.create_table(
                            TableName=container_name,
                            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                            BillingMode='PAY_PER_REQUEST'
                        )
                        table.wait_until_exists()
                        self._tables[container_name] = table
                        logger.info(f'Table "{container_name}" ready.')
                    except Exception as ce:
                        logger.error(f'Failed to create table "{container_name}": {ce}')
                        return None
                else:
                    logger.error(f'Error accessing table "{container_name}": {e}')
                    return None
        return self._tables[container_name]

    def create_item(self, container_name: str, item: dict) -> dict:
        """Insert a new document into a table."""
        try:
            table = self.get_container(container_name)
            if table is None:
                raise ConnectionError('DynamoDB table unavailable.')
            
            # Convert float to Decimal for DynamoDB
            import json
            from decimal import Decimal
            item = json.loads(json.dumps(item), parse_float=Decimal)
            
            table.put_item(Item=item)
            logger.info(f'Created item {item.get("id")} in {container_name}.')
            return item
        except Exception as e:
            logger.error(f'Error creating item in {container_name}: {e}')
            raise

    def get_item(self, container_name: str, item_id: str, partition_key: str = None) -> dict:
        """Read a single document by ID."""
        try:
            table = self.get_container(container_name)
            if table is None:
                return None
            response = table.get_item(Key={'id': item_id})
            return self._to_float(response.get('Item'))
        except Exception as e:
            logger.error(f'Error reading item {item_id} from {container_name}: {e}')
            return None

    def update_item(self, container_name: str, item_id: str, item: dict, partition_key: str = None) -> dict:
        """Replace an existing document (DynamoDB put_item replaces entirely)."""
        return self.create_item(container_name, item)

    def upsert_item(self, container_name: str, item: dict) -> dict:
        """Upsert a document (create or replace)."""
        return self.create_item(container_name, item)

    def delete_item(self, container_name: str, item_id: str, partition_key: str = None):
        """Delete a document by ID."""
        try:
            table = self.get_container(container_name)
            if table is None:
                raise ConnectionError('DynamoDB table unavailable.')
            table.delete_item(Key={'id': item_id})
            logger.info(f'Deleted item {item_id} from {container_name}.')
        except Exception as e:
            logger.error(f'Error deleting item {item_id} from {container_name}: {e}')
            raise

    def query_items(self, container_name: str, query: str,
                    parameters: list = None, partition_key: str = None,
                    enable_cross_partition: bool = True) -> list:
        """
        Emulate Cosmos DB SQL queries using DynamoDB Scan.
        Since we don't want to rewrite all the application services immediately,
        we parse the basic SQL conditions and use boto3 Attr to filter the scan.
        """
        try:
            table = self.get_container(container_name)
            if table is None:
                return []
            
            scan_kwargs = {}
            if 'WHERE' in query.upper():
                where_clause = query[query.upper().index('WHERE') + 5:]
                if 'ORDER BY' in where_clause.upper():
                    where_clause = where_clause[:where_clause.upper().index('ORDER BY')]
                
                # Basic parsing of conditions
                filter_expression = None
                
                # Check for c.id = @id or c.email = @email
                eq_matches = re.findall(r'c\.(\w+)\s*=\s*(@\w+)', where_clause)
                for field, param_name in eq_matches:
                    val = next((p['value'] for p in (parameters or []) if p['name'] == param_name), None)
                    if val is not None:
                        cond = Attr(field).eq(val)
                        filter_expression = cond if filter_expression is None else filter_expression & cond
                
                # Check for CONTAINS(LOWER(c.field), @search)
                contains_matches = re.findall(r'CONTAINS\(LOWER\(c\.(\w+)\),\s*(@\w+)\)', where_clause)
                for field, param_name in contains_matches:
                    val = next((p['value'] for p in (parameters or []) if p['name'] == param_name), None)
                    if val is not None:
                        # DynamoDB doesn't have a case-insensitive contains, so we just use contains
                        # Note: In a real prod environment we'd keep lowercase versions of fields
                        cond = Attr(field).contains(val)
                        filter_expression = cond if filter_expression is None else filter_expression | cond
                        
                if filter_expression:
                    scan_kwargs['FilterExpression'] = filter_expression

            response = table.scan(**scan_kwargs)
            items = self._to_float(response.get('Items', []))
            
            # Handle sorting if ORDER BY is present
            if 'ORDER BY' in query.upper():
                order_clause = query[query.upper().index('ORDER BY') + 8:].strip()
                match = re.match(r'c\.(\w+)\s*(ASC|DESC)?', order_clause, re.IGNORECASE)
                if match:
                    field = match.group(1)
                    direction = match.group(2) or 'ASC'
                    items = sorted(items, key=lambda x: x.get(field, ''), reverse=(direction.upper() == 'DESC'))
                    
            return items
        except Exception as e:
            logger.error(f'Error querying {container_name}: {e}')
            return []

    def query_items_paged(self, container_name: str, query: str,
                          parameters: list = None, page: int = 1,
                          per_page: int = 25) -> tuple:
        """Execute a paginated query. Returns (items, total_count)."""
        items = self.query_items(container_name, query, parameters)
        total = len(items)
        offset = (page - 1) * per_page
        return items[offset:offset + per_page], total

    def count_items(self, container_name: str, query: str = None,
                    parameters: list = None) -> int:
        """Count documents matching a query."""
        if query and 'WHERE' in query.upper():
            return len(self.query_items(container_name, query, parameters))
        else:
            table = self.get_container(container_name)
            if table:
                return table.item_count
            return 0

    def _to_float(self, data):
        """Convert Decimal back to float/int recursively."""
        import decimal
        if isinstance(data, list):
            return [self._to_float(i) for i in data]
        elif isinstance(data, dict):
            return {k: self._to_float(v) for k, v in data.items()}
        elif isinstance(data, decimal.Decimal):
            if data % 1 == 0:
                return int(data)
            return float(data)
        return data

# Singleton instance
dynamodb = DynamoDBService()  # We keep the instance name `dynamodb` to minimize refactoring, but it's DynamoDB!
