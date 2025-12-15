from django.core.management.base import BaseCommand
from trading.models import Portfolio, Stock

class Command(BaseCommand):
    help = 'Clean up corrupted portfolio entries'

    def handle(self, *args, **options):
        self.stdout.write("Cleaning up corrupted portfolio entries...")
        
        deleted_count = 0
        total_count = Portfolio.objects.count()
        
        for portfolio in Portfolio.objects.all():
            should_delete = False
            try:
                # Check if stock exists and has valid data
                if not portfolio.stock:
                    should_delete = True
                    reason = "NULL stock reference"
                elif not portfolio.stock.symbol or portfolio.stock.symbol.strip() == '':
                    should_delete = True
                    reason = "Empty stock symbol"
                elif not portfolio.stock.name or portfolio.stock.name.strip() == '':
                    should_delete = True
                    reason = "Empty stock name"
                
                if should_delete:
                    self.stdout.write(f"Deleting portfolio {portfolio.id}: {reason}")
                    portfolio.delete()
                    deleted_count += 1
                    
            except Exception as e:
                self.stdout.write(f"Deleting corrupted portfolio {portfolio.id}: {str(e)}")
                portfolio.delete()
                deleted_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleanup complete! Deleted {deleted_count} corrupted entries out of {total_count} total.'
            )
        )