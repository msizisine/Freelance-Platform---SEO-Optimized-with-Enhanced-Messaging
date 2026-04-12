from django.core.management.base import BaseCommand
from core.models_payments import ProviderEarnings, PaymentTransaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create missing transactions for all earnings'

    def handle(self, *args, **options):
        # Find all earnings that don't have transactions
        earnings_without_transactions = []
        
        for earning in ProviderEarnings.objects.all():
            transactions = PaymentTransaction.objects.filter(earning=earning)
            if transactions.count() == 0:
                earnings_without_transactions.append(earning)
        
        self.stdout.write(f'Found {len(earnings_without_transactions)} earnings without transactions')
        
        for earning in earnings_without_transactions:
            try:
                # Create earning transaction
                earning_transaction = PaymentTransaction.objects.create(
                    provider=earning.provider,
                    transaction_type='earning',
                    amount=earning.net_amount,
                    status='completed',
                    earning=earning,
                    description=f'Earning from {earning.order.order_number if earning.order else "job"} - Net amount after commission',
                    reference_number=f'EARN-{earning.id.hex[:8].upper()}',
                    processed_at=timezone.now()
                )
                
                # Create commission transaction
                commission_transaction = PaymentTransaction.objects.create(
                    provider=earning.provider,
                    transaction_type='fee',
                    amount=earning.commission_amount,
                    status='completed',
                    earning=earning,
                    description=f'Platform commission from {earning.order.order_number if earning.order else "job"}',
                    reference_number=f'COMM-{earning.id.hex[:8].upper()}',
                    processed_at=timezone.now()
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created transactions for {earning.provider.email} - '
                        f'Earning: R{earning.net_amount}, Commission: R{earning.commission_amount}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to create transactions for earning {earning.id}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Completed. Created transactions for {len(earnings_without_transactions)} earnings.'
            )
        )
