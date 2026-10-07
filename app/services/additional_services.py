"""
Barcode, Report, Forecasting, Notification, and Audit services.
"""

import io
import logging
import uuid
import random
from datetime import datetime, timezone, timedelta

from ..services.dynamodb_service import dynamodb
from ..utils.constants import (CONTAINER_NOTIFICATIONS, CONTAINER_AUDIT_LOGS,
                                CONTAINER_SALES_ORDERS)

logger = logging.getLogger(__name__)


# ==================== BARCODE SERVICE ====================

def generate_barcode(product_id: str, barcode_value: str, barcode_type: str = 'code128') -> str:
    """Generate a barcode image and upload to Blob Storage."""
    try:
        import barcode
        from barcode.writer import ImageWriter
        code_class = barcode.get_barcode_class(barcode_type)
        code = code_class(barcode_value, writer=ImageWriter())
        buffer = io.BytesIO()
        code.write(buffer)
        buffer.seek(0)
        # Upload to blob storage
        try:
            from ..services.s3_service import s3_storage
            from flask import current_app
            container = current_app.config.get('AZURE_BLOB_CONTAINER_IMAGES', 'product-images')
            filename = f"barcodes/{product_id}/{barcode_value}.png"
            url = s3_storage.upload_bytes(container, buffer.getvalue(), filename, 'image/png')
            return url
        except Exception:
            logger.warning('Blob Storage unavailable, barcode not uploaded.')
            return ''
    except Exception as e:
        logger.error(f'Error generating barcode: {e}')
        return ''


def generate_barcode_number() -> str:
    """Generate a unique EAN-13 compatible barcode number."""
    prefix = '200'  # Internal use prefix
    body = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    code = prefix + body
    # Calculate check digit
    total = sum(int(code[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
    check = (10 - (total % 10)) % 10
    return code + str(check)


def lookup_by_barcode(barcode_value: str):
    """Find product by barcode value."""
    from ..services.product_service import get_product_by_barcode
    return get_product_by_barcode(barcode_value)


# ==================== REPORT SERVICE ====================

def generate_pdf_report(title: str, headers: list, data: list, filename: str) -> bytes:
    """Generate a PDF report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Table
        table_data = [headers] + data
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(table)
        doc.build(elements)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f'Error generating PDF: {e}')
        return b''


def generate_excel_report(title: str, headers: list, data: list, filename: str) -> bytes:
    """Generate an Excel report using openpyxl."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = title[:31]  # Max sheet name length

        # Header styling
        header_fill = PatternFill(start_color='4f46e5', end_color='4f46e5', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF', size=11)

        # Write title
        ws['A1'] = title
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws.append([])  # Empty row

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')

        # Write data
        for row_idx, row_data in enumerate(data, 5):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Auto-width columns
        for col in ws.columns:
            max_length = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 30)

        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f'Error generating Excel: {e}')
        return b''


def upload_report_file(data: bytes, filename: str, content_type: str) -> str:
    """Upload a generated report to Blob Storage."""
    try:
        from ..services.s3_service import s3_storage
        return s3_storage.upload_report(data, filename, content_type)
    except Exception as e:
        logger.error(f'Error uploading report: {e}')
        return ''


# ==================== FORECASTING SERVICE ====================

def get_demand_forecast(product_id: str, forecast_days: int = 30) -> dict:
    """Calculate demand forecast using moving averages."""
    try:
        historical = _get_historical_sales(product_id, 180)
        if not historical:
            return {'historical': [], 'forecast': [], 'reorder_point': 0}

        # Simple Moving Average (SMA) - 7-day window
        window = 7
        sma_values = []
        for i in range(len(historical) - window + 1):
            avg = sum(historical[i:i + window]) / window
            sma_values.append(round(avg, 2))

        # Forecast future days using last SMA value
        last_sma = sma_values[-1] if sma_values else 0
        forecast = [round(last_sma * (1 + random.uniform(-0.1, 0.1)), 2) for _ in range(forecast_days)]

        return {
            'historical': historical,
            'forecast': forecast,
            'sma': sma_values,
            'avg_daily_demand': round(sum(historical) / len(historical), 2) if historical else 0,
            'forecast_total': round(sum(forecast), 2)
        }
    except Exception as e:
        logger.error(f'Error calculating forecast: {e}')
        return {'historical': [], 'forecast': [], 'avg_daily_demand': 0}


def get_reorder_suggestions() -> list:
    """Get products that need reordering based on forecast vs current stock."""
    try:
        from ..services.product_service import get_all_products
        from ..services.inventory_service import get_inventory_by_product

        products, _ = get_all_products(page=1, per_page=100)
        suggestions = []

        for product in products:
            inventory = get_inventory_by_product(product.id)
            total_stock = sum(inv.available_quantity for inv in inventory)

            if total_stock <= product.reorder_point:
                suggestions.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku': product.sku,
                    'current_stock': total_stock,
                    'reorder_point': product.reorder_point,
                    'suggested_quantity': product.reorder_quantity,
                    'urgency': 'critical' if total_stock <= product.min_stock_level else 'normal'
                })

        return sorted(suggestions, key=lambda x: x['current_stock'])
    except Exception as e:
        logger.error(f'Error getting reorder suggestions: {e}')
        return []


def get_seasonal_trends(product_id: str) -> dict:
    """Get monthly sales trends."""
    try:
        monthly = {}
        items = dynamodb.query_items(
            CONTAINER_SALES_ORDERS,
            'SELECT c.created_at, c.items FROM c WHERE c.status != "cancelled"'
        )
        for order in items:
            month = order.get('created_at', '')[:7]  # YYYY-MM
            for item in order.get('items', []):
                if item.get('product_id') == product_id:
                    monthly[month] = monthly.get(month, 0) + item.get('quantity', 0)

        return {'months': list(monthly.keys()), 'quantities': list(monthly.values())}
    except Exception as e:
        logger.error(f'Error getting seasonal trends: {e}')
        return {'months': [], 'quantities': []}


def _get_historical_sales(product_id: str, days: int = 90) -> list:
    """Get daily sales quantities for a product."""
    try:
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        items = dynamodb.query_items(
            CONTAINER_SALES_ORDERS,
            'SELECT c.created_at, c.items FROM c WHERE c.created_at >= @start AND c.status != "cancelled"',
            [{'name': '@start', 'value': start_date}]
        )
        daily = {}
        for order in items:
            date = order.get('created_at', '')[:10]
            for item in order.get('items', []):
                if item.get('product_id') == product_id:
                    daily[date] = daily.get(date, 0) + item.get('quantity', 0)
        # Fill in zeros for missing days
        result = []
        current = datetime.now(timezone.utc) - timedelta(days=days)
        for _ in range(days):
            date_str = current.strftime('%Y-%m-%d')
            result.append(daily.get(date_str, 0))
            current += timedelta(days=1)
        return result
    except Exception as e:
        logger.error(f'Error getting historical sales: {e}')
        return []


# ==================== NOTIFICATION SERVICE ====================

def create_notification(user_id, ntype, title, message, severity='info', action_url=''):
    """Create a notification in Cosmos DB."""
    from ..models.notification import Notification
    notif = Notification(
        user_id=user_id, type=ntype, title=title,
        message=message, severity=severity, action_url=action_url
    )
    try:
        dynamodb.create_item(CONTAINER_NOTIFICATIONS, notif.to_dict())
        return notif
    except Exception as e:
        logger.error(f'Error creating notification: {e}')
        return None


def get_user_notifications(user_id, page=1, per_page=20, unread_only=False):
    query = 'SELECT * FROM c WHERE c.user_id = @uid'
    params = [{'name': '@uid', 'value': user_id}]
    if unread_only:
        query += ' AND c.is_read = false'
    query += ' ORDER BY c.created_at DESC'
    items, total = dynamodb.query_items_paged(CONTAINER_NOTIFICATIONS, query, params, page, per_page)
    from ..models.notification import Notification
    return [Notification.from_dict(i) for i in items], total


def get_unread_count(user_id):
    return dynamodb.count_items(
        CONTAINER_NOTIFICATIONS,
        'SELECT VALUE COUNT(1) FROM c WHERE c.user_id = @uid AND c.is_read = false',
        [{'name': '@uid', 'value': user_id}]
    )


def mark_as_read(notification_id, user_id):
    items = dynamodb.query_items(
        CONTAINER_NOTIFICATIONS,
        'SELECT * FROM c WHERE c.id = @id AND c.user_id = @uid',
        [{'name': '@id', 'value': notification_id}, {'name': '@uid', 'value': user_id}]
    )
    if items:
        items[0]['is_read'] = True
        dynamodb.update_item(CONTAINER_NOTIFICATIONS, notification_id, items[0], user_id)
        return True
    return False


def mark_all_as_read(user_id):
    items = dynamodb.query_items(
        CONTAINER_NOTIFICATIONS,
        'SELECT * FROM c WHERE c.user_id = @uid AND c.is_read = false',
        [{'name': '@uid', 'value': user_id}],
        partition_key=user_id
    )
    for item in items:
        item['is_read'] = True
        dynamodb.update_item(CONTAINER_NOTIFICATIONS, item['id'], item, user_id)
    return len(items)


# ==================== AUDIT SERVICE ====================

def create_audit_log(user_id, user_name, action, entity_type, entity_id,
                     changes=None, request_obj=None):
    """Create an audit log entry."""
    from ..models.audit_log import AuditLog
    log = AuditLog(
        user_id=user_id, user_name=user_name, action=action,
        entity_type=entity_type, entity_id=entity_id,
        changes=changes or {},
        ip_address=request_obj.remote_addr if request_obj else '',
        user_agent=str(request_obj.user_agent) if request_obj else ''
    )
    try:
        dynamodb.create_item(CONTAINER_AUDIT_LOGS, log.to_dict())
        return log
    except Exception as e:
        logger.error(f'Error creating audit log: {e}')
        return None


def get_audit_logs(page=1, per_page=25, user_id='', action='',
                   entity_type='', date_from='', date_to=''):
    query = 'SELECT * FROM c WHERE 1=1'
    params = []
    if user_id:
        query += ' AND c.user_id = @uid'
        params.append({'name': '@uid', 'value': user_id})
    if action:
        query += ' AND c.action = @action'
        params.append({'name': '@action', 'value': action})
    if entity_type:
        query += ' AND c.entity_type = @et'
        params.append({'name': '@et', 'value': entity_type})
    if date_from:
        query += ' AND c.timestamp >= @df'
        params.append({'name': '@df', 'value': date_from})
    if date_to:
        query += ' AND c.timestamp <= @dt'
        params.append({'name': '@dt', 'value': date_to})
    query += ' ORDER BY c.timestamp DESC'
    items, total = dynamodb.query_items_paged(CONTAINER_AUDIT_LOGS, query, params, page, per_page)
    from ..models.audit_log import AuditLog
    return [AuditLog.from_dict(i) for i in items], total


def export_audit_logs(filters, fmt='excel'):
    """Export audit logs."""
    logs, _ = get_audit_logs(page=1, per_page=1000, **filters)
    headers = ['Timestamp', 'User', 'Action', 'Entity Type', 'Entity ID', 'IP Address']
    data = [[l.timestamp, l.user_name, l.action, l.entity_type, l.entity_id, l.ip_address] for l in logs]
    if fmt == 'pdf':
        return generate_pdf_report('Audit Logs Report', headers, data, 'audit_logs.pdf')
    return generate_excel_report('Audit Logs Report', headers, data, 'audit_logs.xlsx')
