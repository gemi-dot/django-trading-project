from django.core.management.base import BaseCommand
from trading.models import Portfolio, Stock
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Diagnose and fix portfolio data issues'

    def handle(self, *args, **options):
        self.stdout.write("=== Portfolio Data Diagnosis ===")
        
        # Check all portfolio entries
        portfolios = Portfolio.objects.all()
        self.stdout.write(f"Total portfolio entries: {portfolios.count()}")
        
        problem_entries = []
        
        for portfolio in portfolios:
            try:
                # Try to access stock data
                stock = portfolio.stock
                if not stock:
                    problem_entries.append({
                        'portfolio_id': portfolio.id,
                        'issue': 'NULL stock reference',
                        'portfolio': portfolio
                    })
                elif not stock.symbol or stock.symbol.strip() == '':
                    problem_entries.append({
                        'portfolio_id': portfolio.id,
                        'issue': f'Empty stock symbol: "{stock.symbol}"',
                        'portfolio': portfolio,
                        'stock': stock
                    })
                elif not stock.name or stock.name.strip() == '':
                    problem_entries.append({
                        'portfolio_id': portfolio.id,
                        'issue': f'Empty stock name: "{stock.name}"',
                        'portfolio': portfolio,
                        'stock': stock
                    })
                else:
                    self.stdout.write(f"✓ Portfolio {portfolio.id}: {stock.symbol} ({stock.name}) - {portfolio.quantity} shares")
            except Exception as e:
                problem_entries.append({
                    'portfolio_id': portfolio.id,
                    'issue': f'Error accessing stock: {e}',
                    'portfolio': portfolio
                })
        
        # Report problems
        if problem_entries:
            self.stdout.write(self.style.ERROR(f"\n=== Found {len(problem_entries)} Problem Entries ==="))
            for entry in problem_entries:
                self.stdout.write(self.style.ERROR(f"Portfolio ID {entry['portfolio_id']}: {entry['issue']}"))
                
                # Get user for this portfolio
                try:
                    user = entry['portfolio'].user
                    self.stdout.write(f"  User: {user.username}")
                    self.stdout.write(f"  Quantity: {entry['portfolio'].quantity}")
                    self.stdout.write(f"  Avg Price: {entry['portfolio'].average_price}")
                except Exception as e:
                    self.stdout.write(f"  Error getting user: {e}")
                
                self.stdout.write("")
            
            # Ask if user wants to clean up
            confirm = input("\nDo you want to delete these problematic portfolio entries? (yes/no): ")
            if confirm.lower() == 'yes':
                for entry in problem_entries:
                    try:
                        entry['portfolio'].delete()
                        self.stdout.write(self.style.SUCCESS(f"Deleted portfolio entry {entry['portfolio_id']}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error deleting portfolio {entry['portfolio_id']}: {e}"))
                        
                self.stdout.write(self.style.SUCCESS(f"\nCleanup completed! Deleted {len(problem_entries)} problematic entries."))
            else:
                self.stdout.write("No changes made.")
        else:
            self.stdout.write(self.style.SUCCESS("✓ No portfolio data issues found!"))
        
        # Check for orphaned stocks
        self.stdout.write("\n=== Checking for problematic stocks ===")
        stocks = Stock.objects.all()
        problem_stocks = []
        
        for stock in stocks:
            issues = []
            if not stock.symbol or stock.symbol.strip() == '':
                issues.append("Empty symbol")
            if not stock.name or stock.name.strip() == '':
                issues.append("Empty name")
                
            if issues:
                problem_stocks.append({
                    'stock_id': stock.id,
                    'issues': issues,
                    'stock': stock
                })
        
        if problem_stocks:
            self.stdout.write(self.style.WARNING(f"Found {len(problem_stocks)} problematic stocks:"))
            for entry in problem_stocks:
                self.stdout.write(f"Stock ID {entry['stock_id']}: {', '.join(entry['issues'])}")
                self.stdout.write(f"  Symbol: '{entry['stock'].symbol}' Name: '{entry['stock'].name}'")
        else:
            self.stdout.write(self.style.SUCCESS("✓ No problematic stocks found!"))