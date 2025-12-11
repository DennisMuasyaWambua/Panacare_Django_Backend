from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from healthcare.models import PatientSubscription, Payment
from healthcare.pesapal_client import PesapalClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage subscription renewals and expiration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--expire-subscriptions',
            action='store_true',
            help='Mark expired subscriptions as expired',
        )
        parser.add_argument(
            '--check-renewals',
            action='store_true',
            help='Check for subscription renewals',
        )
        parser.add_argument(
            '--sync-payments',
            action='store_true',
            help='Sync pending payments with Pesapal',
        )
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=7,
            help='Number of days ahead to check for renewals (default: 7)',
        )

    def handle(self, *args, **options):
        if options['expire_subscriptions']:
            self.expire_subscriptions()
        
        if options['check_renewals']:
            self.check_renewals(options['days_ahead'])
        
        if options['sync_payments']:
            self.sync_payments()
        
        if not any([options['expire_subscriptions'], options['check_renewals'], options['sync_payments']]):
            self.stdout.write(
                self.style.WARNING('No action specified. Use --help to see available options.')
            )

    def expire_subscriptions(self):
        """Mark expired subscriptions as expired"""
        today = timezone.now().date()
        
        expired_subscriptions = PatientSubscription.objects.filter(
            status='active',
            end_date__lt=today
        )
        
        count = expired_subscriptions.count()
        
        if count > 0:
            expired_subscriptions.update(status='expired')
            self.stdout.write(
                self.style.SUCCESS(f'Successfully marked {count} subscriptions as expired')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No subscriptions to expire')
            )

    def check_renewals(self, days_ahead):
        """Check for subscriptions that need renewal"""
        today = timezone.now().date()
        renewal_date = today + timedelta(days=days_ahead)
        
        expiring_subscriptions = PatientSubscription.objects.filter(
            status='active',
            end_date__lte=renewal_date,
            end_date__gte=today
        )
        
        count = expiring_subscriptions.count()
        
        if count > 0:
            self.stdout.write(
                self.style.WARNING(f'Found {count} subscriptions expiring in the next {days_ahead} days')
            )
            
            for subscription in expiring_subscriptions:
                self.stdout.write(
                    f'  - Patient: {subscription.patient.user.email}, '
                    f'Package: {subscription.package.name}, '
                    f'Expires: {subscription.end_date}'
                )
                
                # Here you could add logic to send renewal reminders
                # or automatically create renewal payments
                
        else:
            self.stdout.write(
                self.style.SUCCESS(f'No subscriptions expiring in the next {days_ahead} days')
            )

    def sync_payments(self):
        """Sync pending payments with Pesapal"""
        pesapal_client = PesapalClient()
        
        # Get payments that are processing or pending with gateway transaction IDs
        pending_payments = Payment.objects.filter(
            status__in=['processing', 'pending'],
            gateway_transaction_id__isnull=False
        ).exclude(gateway_transaction_id='')
        
        synced_count = 0
        
        for payment in pending_payments:
            try:
                # Get transaction status from Pesapal
                status_response = pesapal_client.get_transaction_status(
                    payment.gateway_transaction_id
                )
                
                if "error" not in status_response:
                    payment.gateway_response = status_response
                    payment_status = status_response.get('payment_status_description', '').upper()
                    
                    old_status = payment.status
                    
                    if payment_status == 'COMPLETED':
                        payment.status = 'completed'
                        payment.save()
                        
                        # Activate associated subscriptions
                        subscriptions = payment.subscriptions.all()
                        for subscription in subscriptions:
                            if subscription.status == 'pending':
                                subscription.status = 'active'
                                subscription.save()
                                
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Payment {payment.reference} completed - activated {subscriptions.count()} subscriptions'
                            )
                        )
                        synced_count += 1
                        
                    elif payment_status in ['FAILED', 'INVALID']:
                        payment.status = 'failed'
                        payment.save()
                        
                        self.stdout.write(
                            self.style.WARNING(
                                f'Payment {payment.reference} failed'
                            )
                        )
                        synced_count += 1
                    
                    elif old_status != payment.status:
                        payment.save()
                        synced_count += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error syncing payment {payment.reference}: {str(e)}'
                    )
                )
        
        if synced_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully synced {synced_count} payments')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No payments to sync')
            )

    def create_renewal_payment(self, subscription):
        """Create a renewal payment for a subscription"""
        try:
            import secrets
            payment_reference = f"REN_{secrets.token_hex(8).upper()}"
            
            payment = Payment.objects.create(
                reference=payment_reference,
                amount=subscription.package.price,
                payment_method='pesapal',
                status='pending'
            )
            
            # Create new subscription for renewal
            new_subscription = PatientSubscription.objects.create(
                patient=subscription.patient,
                package=subscription.package,
                payment=payment,
                start_date=subscription.end_date + timedelta(days=1),
                end_date=subscription.end_date + timedelta(days=subscription.package.duration_days + 1),
                status='pending'
            )
            
            return payment, new_subscription
            
        except Exception as e:
            logger.error(f"Error creating renewal payment: {str(e)}")
            return None, None