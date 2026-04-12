from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order
from core.models_receipts import PaymentReceipt
import random
import string


class Command(BaseCommand):
    help = 'Generate payment receipts for existing paid orders that don\'t have receipts'

    def handle(self, *args, **options):
        """Generate payment receipts for paid orders without receipts"""
        
        # Get all paid orders
        paid_orders = Order.objects.filter(payment_status='paid')
        
        # Filter orders that don't have payment receipts
        orders_without_receipts = []
        for order in paid_orders:
            if not PaymentReceipt.objects.filter(order=order).exists():
                orders_without_receipts.append(order)
        
        self.stdout.write(f"Found {len(orders_without_receipts)} paid orders without payment receipts")
        
        # Map payment methods
        payment_method_map = {
            'ozow': 'ozow',
            'eft': 'eft', 
            'in_person': 'cash',
            'yoco': 'card'
        }
        
        created_count = 0
        
        for order in orders_without_receipts:
            try:
                # Generate receipt number
                receipt_number = 'REC-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                # Get payment method
                receipt_method = payment_method_map.get(order.payment_method, 'other')
                
                # Create payment receipt
                receipt = PaymentReceipt.objects.create(
                    homeowner=order.homeowner,
                    order=order,
                    payment_method=receipt_method,
                    payment_status='completed',
                    amount=order.total_amount,
                    receipt_number=receipt_number,
                    payment_date=timezone.now(),
                    description=f"Payment for Order {order.order_number} - {order.gig.title}",
                    confirmed_at=timezone.now()
                )
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created receipt {receipt.receipt_number} for Order {order.order_number} "
                        f"({order.homeowner.email}) - R{order.total_amount}"
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to create receipt for Order {order.order_number}: {str(e)}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} payment receipts"
            )
        )
