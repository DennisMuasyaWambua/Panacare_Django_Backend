from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import PatientSubscription, Package, Payment
from .pesapal_client import PesapalClient
import secrets
import logging

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """
    Utility class for managing subscription operations like upgrades, downgrades, and renewals.
    """
    
    def __init__(self):
        self.pesapal_client = PesapalClient()
    
    def calculate_prorated_amount(self, current_subscription, new_package):
        """
        Calculate prorated amount for subscription upgrade/downgrade.
        
        Args:
            current_subscription: Current PatientSubscription instance
            new_package: New Package instance
            
        Returns:
            tuple: (prorated_amount, remaining_days)
        """
        today = timezone.now().date()
        
        # Calculate remaining days in current subscription
        remaining_days = (current_subscription.end_date - today).days
        
        if remaining_days <= 0:
            return Decimal('0.00'), 0
        
        # Calculate daily rate for current package
        current_daily_rate = current_subscription.package.price / current_subscription.package.duration_days
        
        # Calculate daily rate for new package
        new_daily_rate = new_package.price / new_package.duration_days
        
        # Calculate unused amount from current subscription
        unused_amount = current_daily_rate * remaining_days
        
        # Calculate amount needed for new package for remaining days
        new_amount_needed = new_daily_rate * remaining_days
        
        # Calculate prorated amount (can be positive for upgrade, negative for downgrade)
        prorated_amount = new_amount_needed - unused_amount
        
        return prorated_amount, remaining_days
    
    def upgrade_subscription(self, patient, new_package_id):
        """
        Upgrade a patient's subscription to a higher-tier package.
        
        Args:
            patient: Patient instance
            new_package_id: ID of the new package
            
        Returns:
            dict: Result of the upgrade operation
        """
        try:
            # Get current active subscription
            current_subscription = PatientSubscription.objects.filter(
                patient=patient,
                status='active',
                end_date__gte=timezone.now().date()
            ).first()
            
            if not current_subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found'
                }
            
            # Get new package
            try:
                new_package = Package.objects.get(id=new_package_id, is_active=True)
            except Package.DoesNotExist:
                return {
                    'success': False,
                    'error': 'New package not found or inactive'
                }
            
            # Check if it's actually an upgrade (higher price)
            if new_package.price <= current_subscription.package.price:
                return {
                    'success': False,
                    'error': 'New package must be higher-tier than current package'
                }
            
            # Calculate prorated amount
            prorated_amount, remaining_days = self.calculate_prorated_amount(
                current_subscription, new_package
            )
            
            if prorated_amount <= 0:
                return {
                    'success': False,
                    'error': 'No additional payment required for upgrade'
                }
            
            # Create payment for upgrade
            payment_reference = f"UPG_{secrets.token_hex(8).upper()}"
            
            with transaction.atomic():
                payment = Payment.objects.create(
                    reference=payment_reference,
                    amount=prorated_amount,
                    payment_method='pesapal',
                    status='pending'
                )
                
                # Store current subscription ID in payment metadata for cancellation after payment
                payment.gateway_response = {
                    'upgrade_cancel_subscription_id': str(current_subscription.id)
                }
                payment.save()
                
                # Keep current subscription active until payment is completed
                # It will be cancelled via IPN webhook after successful payment
                
                # Create new subscription
                new_subscription = PatientSubscription.objects.create(
                    patient=patient,
                    package=new_package,
                    payment=payment,
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timedelta(days=remaining_days),
                    status='pending'
                )
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'payment_reference': payment_reference,
                    'prorated_amount': prorated_amount,
                    'remaining_days': remaining_days,
                    'new_subscription': new_subscription,
                    'message': 'Upgrade initiated. Please complete payment.'
                }
                
        except Exception as e:
            logger.error(f"Error upgrading subscription: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process upgrade'
            }
    
    def downgrade_subscription(self, patient, new_package_id):
        """
        Downgrade a patient's subscription to a lower-tier package.
        
        Args:
            patient: Patient instance
            new_package_id: ID of the new package
            
        Returns:
            dict: Result of the downgrade operation
        """
        try:
            # Get current active subscription
            current_subscription = PatientSubscription.objects.filter(
                patient=patient,
                status='active',
                end_date__gte=timezone.now().date()
            ).first()
            
            if not current_subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found'
                }
            
            # Get new package
            try:
                new_package = Package.objects.get(id=new_package_id, is_active=True)
            except Package.DoesNotExist:
                return {
                    'success': False,
                    'error': 'New package not found or inactive'
                }
            
            # Check if it's actually a downgrade (lower price)
            if new_package.price >= current_subscription.package.price:
                return {
                    'success': False,
                    'error': 'New package must be lower-tier than current package'
                }
            
            # Calculate prorated amount (will be negative for downgrade)
            prorated_amount, remaining_days = self.calculate_prorated_amount(
                current_subscription, new_package
            )
            
            # For downgrade, we typically schedule the change for the next billing cycle
            # rather than providing refunds immediately
            
            with transaction.atomic():
                # Update current subscription to expire at the end of current period
                current_subscription.status = 'active'  # Keep active until end
                current_subscription.save()
                
                # Create new subscription to start after current one ends
                new_subscription = PatientSubscription.objects.create(
                    patient=patient,
                    package=new_package,
                    payment=None,  # No payment needed for downgrade
                    start_date=current_subscription.end_date + timedelta(days=1),
                    end_date=current_subscription.end_date + timedelta(days=new_package.duration_days + 1),
                    status='scheduled'  # New status for scheduled changes
                )
                
                return {
                    'success': True,
                    'new_subscription': new_subscription,
                    'effective_date': new_subscription.start_date,
                    'credit_amount': abs(prorated_amount) if prorated_amount < 0 else 0,
                    'message': f'Downgrade scheduled for {new_subscription.start_date}. Current subscription remains active until {current_subscription.end_date}.'
                }
                
        except Exception as e:
            logger.error(f"Error downgrading subscription: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process downgrade'
            }
    
    def renew_subscription(self, subscription):
        """
        Renew a subscription for another period.
        
        Args:
            subscription: PatientSubscription instance
            
        Returns:
            dict: Result of the renewal operation
        """
        try:
            # Create payment for renewal
            payment_reference = f"REN_{secrets.token_hex(8).upper()}"
            
            with transaction.atomic():
                payment = Payment.objects.create(
                    reference=payment_reference,
                    amount=subscription.package.price,
                    payment_method='pesapal',
                    status='pending'
                )
                
                # Extend current subscription
                subscription.end_date = subscription.end_date + timedelta(days=subscription.package.duration_days)
                subscription.save()
                
                # Link payment to subscription
                payment.subscriptions.add(subscription)
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'payment_reference': payment_reference,
                    'new_end_date': subscription.end_date,
                    'message': 'Renewal initiated. Please complete payment.'
                }
                
        except Exception as e:
            logger.error(f"Error renewing subscription: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to process renewal'
            }
    
    def cancel_subscription(self, subscription, reason=None):
        """
        Cancel a subscription.
        
        Args:
            subscription: PatientSubscription instance
            reason: Optional cancellation reason
            
        Returns:
            dict: Result of the cancellation
        """
        try:
            with transaction.atomic():
                subscription.status = 'cancelled'
                subscription.save()
                
                # You might want to log the cancellation reason
                if reason:
                    logger.info(f"Subscription {subscription.id} cancelled: {reason}")
                
                return {
                    'success': True,
                    'message': 'Subscription cancelled successfully'
                }
                
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to cancel subscription'
            }
    
    def get_subscription_usage(self, subscription):
        """
        Get usage statistics for a subscription.
        
        Args:
            subscription: PatientSubscription instance
            
        Returns:
            dict: Usage statistics
        """
        try:
            # Calculate usage based on consultations
            total_consultations = subscription.consultations_used
            max_consultations = subscription.package.max_consultations
            
            # Calculate days used
            today = timezone.now().date()
            days_used = (today - subscription.start_date).days
            total_days = subscription.package.duration_days
            
            return {
                'consultations_used': total_consultations,
                'max_consultations': max_consultations,
                'consultations_remaining': max_consultations - total_consultations,
                'days_used': days_used,
                'total_days': total_days,
                'days_remaining': (subscription.end_date - today).days,
                'usage_percentage': (total_consultations / max_consultations) * 100 if max_consultations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription usage: {str(e)}")
            return {
                'error': 'Failed to get usage statistics'
            }