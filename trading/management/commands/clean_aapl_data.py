from django.core.management.base import BaseCommand
from trading.models import Portfolio, Trade, StopLossOrder, Watchlist, Stock
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Clean all AAPL data from portfolio, trades, and related records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            default='AAPL',
            help='Stock symbol to clean (default: AAPL)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        symbol = options['symbol'].upper()
        confirm = options['confirm']
        
        self.stdout.write(f"Cleaning all {symbol} data from the database...")
        
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Stock {symbol} not found in database"))
            return
        
        # Count records to be deleted
        portfolio_count = Portfolio.objects.filter(stock=stock).count()
        trade_count = Trade.objects.filter(stock=stock).count()
        stop_loss_count = StopLossOrder.objects.filter(stock=stock).count()
        watchlist_count = Watchlist.objects.filter(stock=stock).count()
        
        self.stdout.write(f"\nFound the following {symbol} records:")
        self.stdout.write(f"  Portfolio holdings: {portfolio_count}")
        self.stdout.write(f"  Trade records: {trade_count}")
        self.stdout.write(f"  Stop loss orders: {stop_loss_count}")
        self.stdout.write(f"  Watchlist entries: {watchlist_count}")
        
        if portfolio_count == 0 and trade_count == 0 and stop_loss_count == 0 and watchlist_count == 0:
            self.stdout.write(self.style.SUCCESS(f"No {symbol} data found to clean!"))
            return
        
        # Show detailed breakdown by user
        self.stdout.write(f"\nDetailed breakdown:")
        
        # Portfolio holdings by user
        portfolios = Portfolio.objects.filter(stock=stock)
        if portfolios.exists():
            self.stdout.write("Portfolio holdings:")
            for portfolio in portfolios:
                self.stdout.write(f"  User: {portfolio.user.username}, Quantity: {portfolio.quantity}, Avg Price: ${portfolio.average_price}")
        
        # Recent trades by user
        trades = Trade.objects.filter(stock=stock).order_by('-order_date')[:10]
        if trades.exists():
            self.stdout.write("Recent trades (last 10):")
            for trade in trades:
                self.stdout.write(f"  {trade.order_date.strftime('%Y-%m-%d')} - {trade.user.username}: {trade.trade_type.upper()} {trade.quantity} @ ${trade.price}")
        
        # Ask for confirmation unless --confirm flag is used
        if not confirm:
            confirm_input = input(f"\nAre you sure you want to delete ALL {symbol} data? This cannot be undone. (yes/no): ")
            if confirm_input.lower() != 'yes':
                self.stdout.write("Operation cancelled.")
                return
        
        # Start deletion process
        self.stdout.write(f"\nStarting cleanup of {symbol} data...")
        
        deleted_counts = {
            'portfolio': 0,
            'trades': 0,
            'stop_loss': 0,
            'watchlist': 0
        }
        
        # Delete portfolio holdings
        if portfolio_count > 0:
            deleted_portfolio = Portfolio.objects.filter(stock=stock).delete()
            deleted_counts['portfolio'] = deleted_portfolio[0]
            self.stdout.write(f"✓ Deleted {deleted_counts['portfolio']} portfolio holdings")
        
        # Delete trade records
        if trade_count > 0:
            deleted_trades = Trade.objects.filter(stock=stock).delete()
            deleted_counts['trades'] = deleted_trades[0]
            self.stdout.write(f"✓ Deleted {deleted_counts['trades']} trade records")
        
        # Delete stop loss orders
        if stop_loss_count > 0:
            deleted_stop_loss = StopLossOrder.objects.filter(stock=stock).delete()
            deleted_counts['stop_loss'] = deleted_stop_loss[0]
            self.stdout.write(f"✓ Deleted {deleted_counts['stop_loss']} stop loss orders")
        
        # Delete watchlist entries
        if watchlist_count > 0:
            deleted_watchlist = Watchlist.objects.filter(stock=stock).delete()
            deleted_counts['watchlist'] = deleted_watchlist[0]
            self.stdout.write(f"✓ Deleted {deleted_counts['watchlist']} watchlist entries")
        
        # Summary
        total_deleted = sum(deleted_counts.values())
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Cleanup complete! Deleted {total_deleted} total {symbol} records.'
            )
        )
        self.stdout.write(f"  Portfolio holdings: {deleted_counts['portfolio']}")
        self.stdout.write(f"  Trade records: {deleted_counts['trades']}")
        self.stdout.write(f"  Stop loss orders: {deleted_counts['stop_loss']}")
        self.stdout.write(f"  Watchlist entries: {deleted_counts['watchlist']}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 {symbol} data cleaned! You can now start fresh with new transactions.")
        )