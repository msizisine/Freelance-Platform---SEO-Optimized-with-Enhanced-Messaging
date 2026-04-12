from django.core.management.base import BaseCommand
from orders.models import Order
from core.models import User
from core.models_payments import ProviderEarnings
from decimal import Decimal
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create missing earnings for paid and completed orders'

    def handle(self, *args, **options):
        # Find paid and completed orders that don't have earnings
        orders_without_earnings = []
        
        for order in Order.objects.filter(payment_status='paid', status='completed'):
            earnings = ProviderEarnings.objects.filter(order=order, provider=order.service_provider)
            if earnings.count() == 0:
                orders_without_earnings.append(order)
        
        self.stdout.write(f'Found {len(orders_without_earnings)} paid/completed orders without earnings')
        
        # Create earnings for each order
        for order in orders_without_earnings:
            try:
                # Calculate commission (10% default)
                commission_rate = Decimal('0.10')
                commission_amount = order.total_amount * commission_rate
                net_amount = order.total_amount - commission_amount
                
                # Create earning record
                earning = ProviderEarnings.objects.create(
                    provider=order.service_provider,
                    order=order,
                    gross_amount=order.total_amount,
                    commission_amount=commission_amount,
                    net_amount=net_amount,
                    earning_type='job_completion',
                    status='available',  # Available immediately since order is paid
                    description=f'Earnings from completed order {order.order_number}',
                    available_at=timezone.now()  # Available immediately
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created earning for {order.service_provider.email} - '
                        f'Order {order.order_number} - Gross: R{order.total_amount}, '
                        f'Net: R{net_amount}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to create earning for Order {order.order_number}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed. Created earnings for {len(orders_without_earnings)} orders.'
            )
        )
