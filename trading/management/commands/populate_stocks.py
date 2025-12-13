from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from trading.models import Stock, StockPrice

class Command(BaseCommand):
    help = 'Populate the database with sample stock data'

    def handle(self, *args, **options):
        # Sample stock data
        stocks_data = [
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'market_cap': 3000000000000,  # $3T
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'market_cap': 1700000000000,  # $1.7T
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Software',
                'market_cap': 2800000000000,  # $2.8T
            },
            {
                'symbol': 'AMZN',
                'name': 'Amazon.com Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Consumer Discretionary',
                'industry': 'E-commerce',
                'market_cap': 1600000000000,  # $1.6T
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'exchange': 'NASDAQ',
                'sector': 'Consumer Discretionary',
                'industry': 'Electric Vehicles',
                'market_cap': 800000000000,  # $800B
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'exchange': 'NASDAQ',
                'sector': 'Technology',
                'industry': 'Semiconductors',
                'market_cap': 1800000000000,  # $1.8T
            },
            {
                'symbol': 'JPM',
                'name': 'JPMorgan Chase & Co.',
                'exchange': 'NYSE',
                'sector': 'Financial Services',
                'industry': 'Banking',
                'market_cap': 500000000000,  # $500B
            },
            {
                'symbol': 'JNJ',
                'name': 'Johnson & Johnson',
                'exchange': 'NYSE',
                'sector': 'Healthcare',
                'industry': 'Pharmaceuticals',
                'market_cap': 450000000000,  # $450B
            },
            {
                'symbol': 'V',
                'name': 'Visa Inc.',
                'exchange': 'NYSE',
                'sector': 'Financial Services',
                'industry': 'Payment Processing',
                'market_cap': 500000000000,  # $500B
            },
            {
                'symbol': 'WMT',
                'name': 'Walmart Inc.',
                'exchange': 'NYSE',
                'sector': 'Consumer Staples',
                'industry': 'Retail',
                'market_cap': 600000000000,  # $600B
            },
            {
                'symbol': 'PG',
                'name': 'Procter & Gamble Co.',
                'exchange': 'NYSE',
                'sector': 'Consumer Staples',
                'industry': 'Consumer Goods',
                'market_cap': 380000000000,  # $380B
            },
            {
                'symbol': 'HD',
                'name': 'The Home Depot Inc.',
                'exchange': 'NYSE',
                'sector': 'Consumer Discretionary',
                'industry': 'Home Improvement',
                'market_cap': 400000000000,  # $400B
            },
        ]

        # Base prices for each stock (realistic 2024 prices)
        base_prices = {
            'AAPL': 195.00,
            'GOOGL': 140.00,
            'MSFT': 415.00,
            'AMZN': 155.00,
            'TSLA': 250.00,
            'NVDA': 875.00,
            'JPM': 175.00,
            'JNJ': 160.00,
            'V': 275.00,
            'WMT': 165.00,
            'PG': 155.00,
            'HD': 385.00,
        }

        self.stdout.write('Creating stocks...')
        
        for stock_data in stocks_data:
            symbol = stock_data['symbol']
            base_price = Decimal(str(base_prices[symbol]))
            
            # Generate realistic current price (±5% from base)
            price_variation = random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + Decimal(str(price_variation)))
            
            # Calculate price change
            price_change = current_price - base_price
            price_change_percent = (price_change / base_price) * 100
            
            # Generate volume
            volume = random.randint(1000000, 50000000)
            
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': stock_data['name'],
                    'exchange': stock_data['exchange'],
                    'sector': stock_data['sector'],
                    'industry': stock_data['industry'],
                    'market_cap': stock_data['market_cap'],
                    'current_price': current_price,
                    'price_change': price_change,
                    'price_change_percent': price_change_percent,
                    'volume': volume,
                }
            )
            
            if created:
                self.stdout.write(f'  Created {symbol} - {stock_data["name"]}')
                
                # Create historical price data (last 30 days)
                self.create_historical_data(stock, base_price)
            else:
                # Update existing stock with new prices
                stock.current_price = current_price
                stock.price_change = price_change
                stock.price_change_percent = price_change_percent
                stock.volume = volume
                stock.save()
                self.stdout.write(f'  Updated {symbol} - {stock_data["name"]}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {len(stocks_data)} stocks'
            )
        )

    def create_historical_data(self, stock, base_price):
        """Create 30 days of historical price data"""
        from datetime import date, timedelta
        
        current_date = date.today()
        price = base_price
        
        for i in range(30, 0, -1):  # Last 30 days
            historical_date = current_date - timedelta(days=i)
            
            # Generate realistic OHLC data
            daily_variation = random.uniform(-0.03, 0.03)  # ±3% daily variation
            
            open_price = price * (1 + Decimal(str(random.uniform(-0.01, 0.01))))
            high_price = open_price * (1 + Decimal(str(random.uniform(0.005, 0.02))))
            low_price = open_price * (1 - Decimal(str(random.uniform(0.005, 0.02))))
            close_price = open_price * (1 + Decimal(str(daily_variation)))
            
            volume = random.randint(1000000, 30000000)
            
            StockPrice.objects.get_or_create(
                stock=stock,
                date=historical_date,
                defaults={
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume,
                    'adjusted_close': close_price,
                }
            )
            
            # Update price for next iteration
            price = close_price