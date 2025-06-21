"""
Example Stripe webhook handlers.

This module demonstrates how to use the Smart API webhook system
with Stripe webhooks for various payment events.
"""

import logging
from typing import Dict, Any

from ..core.webhook_schema import WebhookEvent
from .decorators import webhook_handler, webhook_middleware
from .handlers import WebhookHandler

logger = logging.getLogger(__name__)


# Function-based handlers using decorators
@webhook_handler('stripe', 'payment_intent.succeeded')
def handle_successful_payment(event: WebhookEvent) -> Dict[str, Any]:
    """Handle successful payment intent."""
    payment_intent = event.payload['data']['object']
    
    logger.info(f"Payment succeeded: {payment_intent['id']} for ${payment_intent['amount']/100}")
    
    # Your business logic here
    # - Update order status
    # - Send confirmation email
    # - Update user account
    
    return {
        'processed': True,
        'payment_id': payment_intent['id'],
        'amount': payment_intent['amount'],
        'currency': payment_intent['currency']
    }


@webhook_handler('stripe', 'payment_intent.payment_failed')
def handle_failed_payment(event: WebhookEvent) -> Dict[str, Any]:
    """Handle failed payment intent."""
    payment_intent = event.payload['data']['object']
    
    logger.warning(f"Payment failed: {payment_intent['id']}")
    
    # Your business logic here
    # - Mark order as failed
    # - Send failure notification
    # - Retry payment logic
    
    return {
        'processed': True,
        'payment_id': payment_intent['id'],
        'status': 'failed',
        'last_payment_error': payment_intent.get('last_payment_error')
    }


@webhook_handler('stripe', 'customer.subscription.created')
def handle_subscription_created(event: WebhookEvent) -> Dict[str, Any]:
    """Handle new subscription creation."""
    subscription = event.payload['data']['object']
    
    logger.info(f"New subscription created: {subscription['id']}")
    
    # Your business logic here
    # - Activate user account
    # - Send welcome email
    # - Set up user permissions
    
    return {
        'processed': True,
        'subscription_id': subscription['id'],
        'customer_id': subscription['customer'],
        'status': subscription['status']
    }


@webhook_handler('stripe', 'invoice.payment_succeeded')
def handle_invoice_payment_succeeded(event: WebhookEvent) -> Dict[str, Any]:
    """Handle successful invoice payment."""
    invoice = event.payload['data']['object']
    
    logger.info(f"Invoice payment succeeded: {invoice['id']}")
    
    # Your business logic here
    # - Update billing records
    # - Send receipt
    # - Extend service period
    
    return {
        'processed': True,
        'invoice_id': invoice['id'],
        'amount_paid': invoice['amount_paid'],
        'customer_id': invoice['customer']
    }


# Middleware example
@webhook_middleware('stripe')
def log_stripe_webhooks(event: WebhookEvent):
    """Log all Stripe webhook events."""
    logger.info(f"Stripe webhook received: {event.type} - {event.id}")
    
    # Add custom headers or metadata
    event.headers['X-Processed-At'] = str(event.timestamp)
    
    # Return None to continue processing
    return None


# Class-based handler example
class AdvancedStripeWebhookHandler(WebhookHandler):
    """
    Advanced Stripe webhook handler with comprehensive event handling.
    
    Usage:
        # Initialize the handler (this registers all on_* methods)
        handler = AdvancedStripeWebhookHandler()
    """
    
    provider = 'stripe'
    
    def on_payment_intent_succeeded(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle successful payment with advanced logic."""
        payment_intent = event.payload['data']['object']
        
        # Extract metadata for business context
        metadata = payment_intent.get('metadata', {})
        order_id = metadata.get('order_id')
        user_id = metadata.get('user_id')
        
        logger.info(f"Payment succeeded for order {order_id}, user {user_id}")
        
        # Advanced business logic
        result = self._process_successful_payment(payment_intent, order_id, user_id)
        
        return self.success_response({
            'payment_id': payment_intent['id'],
            'order_id': order_id,
            'user_id': user_id,
            'processing_result': result
        })
    
    def on_payment_intent_payment_failed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle failed payment with retry logic."""
        payment_intent = event.payload['data']['object']
        
        # Check if this is a retryable failure
        last_error = payment_intent.get('last_payment_error', {})
        error_code = last_error.get('code')
        
        if self._is_retryable_error(error_code):
            logger.info(f"Retryable payment failure: {payment_intent['id']}")
            self._schedule_payment_retry(payment_intent)
        else:
            logger.error(f"Non-retryable payment failure: {payment_intent['id']}")
            self._handle_permanent_failure(payment_intent)
        
        return self.success_response({
            'payment_id': payment_intent['id'],
            'error_code': error_code,
            'retryable': self._is_retryable_error(error_code)
        })
    
    def on_customer_subscription_updated(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle subscription updates."""
        subscription = event.payload['data']['object']
        previous_attributes = event.payload.get('data', {}).get('previous_attributes', {})
        
        # Check what changed
        changes = []
        if 'status' in previous_attributes:
            changes.append(f"status: {previous_attributes['status']} -> {subscription['status']}")
        
        if 'items' in previous_attributes:
            changes.append("subscription items updated")
        
        logger.info(f"Subscription updated: {subscription['id']} - {', '.join(changes)}")
        
        return self.success_response({
            'subscription_id': subscription['id'],
            'changes': changes,
            'current_status': subscription['status']
        })
    
    def on_invoice_payment_failed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle failed invoice payments."""
        invoice = event.payload['data']['object']
        
        # Check attempt count
        attempt_count = invoice.get('attempt_count', 0)
        
        if attempt_count >= 3:
            logger.warning(f"Invoice payment failed after {attempt_count} attempts: {invoice['id']}")
            self._handle_final_invoice_failure(invoice)
        else:
            logger.info(f"Invoice payment failed (attempt {attempt_count}): {invoice['id']}")
        
        return self.success_response({
            'invoice_id': invoice['id'],
            'attempt_count': attempt_count,
            'final_failure': attempt_count >= 3
        })
    
    def on_checkout_session_completed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle completed checkout sessions."""
        session = event.payload['data']['object']
        
        logger.info(f"Checkout session completed: {session['id']}")
        
        # Process the completed checkout
        self._fulfill_checkout_order(session)
        
        return self.success_response({
            'session_id': session['id'],
            'customer_id': session.get('customer'),
            'payment_status': session['payment_status']
        })
    
    # Helper methods
    def _process_successful_payment(self, payment_intent: Dict, order_id: str, user_id: str):
        """Process successful payment business logic."""
        # Implement your business logic here
        # - Update database
        # - Send notifications
        # - Fulfill order
        return {'status': 'processed', 'timestamp': str(payment_intent.get('created'))}
    
    def _is_retryable_error(self, error_code: str) -> bool:
        """Check if payment error is retryable."""
        retryable_codes = [
            'card_declined',
            'insufficient_funds',
            'processing_error'
        ]
        return error_code in retryable_codes
    
    def _schedule_payment_retry(self, payment_intent: Dict):
        """Schedule payment retry logic."""
        # Implement retry scheduling
        logger.info(f"Scheduling retry for payment: {payment_intent['id']}")
    
    def _handle_permanent_failure(self, payment_intent: Dict):
        """Handle permanent payment failures."""
        # Implement permanent failure handling
        logger.error(f"Permanent failure for payment: {payment_intent['id']}")
    
    def _handle_final_invoice_failure(self, invoice: Dict):
        """Handle final invoice payment failure."""
        # Implement final failure logic
        # - Cancel subscription
        # - Send notification
        logger.warning(f"Final invoice failure: {invoice['id']}")
    
    def _fulfill_checkout_order(self, session: Dict):
        """Fulfill order from checkout session."""
        # Implement order fulfillment
        logger.info(f"Fulfilling order from session: {session['id']}")


# Initialize the advanced handler
# This will automatically register all the on_* methods
advanced_stripe_handler = AdvancedStripeWebhookHandler() 