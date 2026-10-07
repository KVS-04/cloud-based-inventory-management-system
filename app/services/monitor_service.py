"""
Monitoring Service - Standard logging integration.
Provides telemetry, custom events, metrics, and exception tracking via standard logging.
When deployed on AWS, these stdout logs are automatically ingested by Amazon CloudWatch for free.
"""

import logging
import json

logger = logging.getLogger(__name__)

class MonitorService:
    """Application monitoring and telemetry via standard logging."""

    _instance = None
    _is_configured = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def setup_flask_middleware(self, app):
        """Setup logging configuration for the Flask app."""
        # For Option A, we don't need any complex middleware, just standard logging.
        self._is_configured = True
        logger.info('Standard monitoring configured. Ready for AWS CloudWatch logs.')

    def track_event(self, name: str, properties: dict = None, measurements: dict = None):
        """Log a custom event."""
        event_data = {
            'event': name,
            'properties': properties or {},
            'measurements': measurements or {}
        }
        logger.info(f'[EVENT] {json.dumps(event_data)}')

    def track_exception(self, exception: Exception, properties: dict = None):
        """Log an exception."""
        logger.exception(f'[EXCEPTION] {exception} | Context: {properties}', exc_info=exception)

    def track_metric(self, name: str, value: float, properties: dict = None):
        """Log a custom metric."""
        metric_data = {
            'metric': name,
            'value': value,
            'properties': properties or {}
        }
        logger.info(f'[METRIC] {json.dumps(metric_data)}')

    def log_info(self, message: str, properties: dict = None):
        """Info-level log."""
        logger.info(f'[INFO] {message} | {properties}')

    def log_warning(self, message: str, properties: dict = None):
        """Warning-level log."""
        logger.warning(f'[WARNING] {message} | {properties}')

    def log_error(self, message: str, properties: dict = None):
        """Error-level log."""
        logger.error(f'[ERROR] {message} | {properties}')

    # --- Predefined Events ---
    def log_login(self, user_id: str, email: str, success: bool):
        self.track_event('UserLogin', {
            'user_id': user_id, 'email': email, 'success': str(success)
        })

    def log_order_created(self, order_number: str, order_type: str, total: float):
        self.track_event('OrderCreated', {
            'order_number': order_number, 'order_type': order_type
        }, {'total_amount': total})

    def log_stock_alert(self, product_id: str, product_name: str, current_stock: int):
        self.track_event('LowStockAlert', {
            'product_id': product_id, 'product_name': product_name
        }, {'current_stock': float(current_stock)})

    def log_report_generated(self, report_type: str, user_id: str):
        self.track_event('ReportGenerated', {
            'report_type': report_type, 'user_id': user_id
        })


# Singleton instance
monitor = MonitorService()
