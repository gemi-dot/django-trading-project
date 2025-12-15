from django.core.management.base import BaseCommand
from trading.models import Portfolio, Trade, StopLossOrder, Watchlist, Stock

class Command(BaseCommand):
    help = 'Remove MSF stock and all related data'

    def handle(self, *args, **options):
        symbol = 'MSF'
        
        self.stdout.write(f"Removing {symbol} stock and all related data...")
        
        try:
            stock = Stock.objects.get(symbol=symbol)
            self.stdout.write(f"Found stock: {stock.symbol} - {stock.name}")
            
            # Count related records
            portfolio_count = Portfolio.objects.filter(stock=stock).count()
            trade_count = Trade.objects.filter(stock=stock).count()
            stop_loss_count = StopLossOrder.objects.filter(stock=stock).count()
            watchlist_count = Watchlist.objects.filter(stock=stock).count()
            
            self.stdout.write(f"Related records found:")
            self.stdout.write(f"  Portfolio holdings: {portfolio_count}")
            self.stdout.write(f"  Trade records: {trade_count}")
            self.stdout.write(f"  Stop loss orders: {stop_loss_count}")
            self.stdout.write(f"  Watchlist entries: {watchlist_count}")
            
            # Delete all related data first
            Portfolio.objects.filter(stock=stock).delete()
            Trade.objects.filter(stock=stock).delete()
            StopLossOrder.objects.filter(stock=stock).delete()
            Watchlist.objects.filter(stock=stock).delete()
            
            # Delete technical indicators if they exist
            try:
                from trading.models import TechnicalIndicators
                TechnicalIndicators.objects.filter(stock=stock).delete()
                self.stdout.write("✓ Deleted technical indicators")
            except:
                pass
            
            # Finally delete the stock itself
            stock.delete()
            
            self.stdout.write(self.style.SUCCESS(f"✓ Successfully removed {symbol} and all related data!"))
            
        except Stock.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Stock {symbol} not found in database"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error removing {symbol}: {str(e)}"))