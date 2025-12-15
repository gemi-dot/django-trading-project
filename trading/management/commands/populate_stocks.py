from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta
from trading.models import Stock, StockPrice

class Command(BaseCommand):
    help = 'Populate the database with sample stock data including PSE stocks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--market',
            type=str,
            choices=['us', 'pse', 'all'],
            default='all',
            help='Which market stocks to populate (us, pse, or all)'
        )
        parser.add_argument(
            '--simulate',
            action='store_true',
            help='Generate historical price data for simulation'
        )

    def handle(self, *args, **options):
        market = options['market']
        simulate = options['simulate']
        
        if market in ['us', 'all']:
            self.populate_us_stocks()
            
        if market in ['pse', 'all']:
            self.populate_pse_stocks()
            
        if simulate:
            self.generate_historical_data()
            self.stdout.write(self.style.SUCCESS('Generated historical price data for simulation'))

    def populate_us_stocks(self):
        # Sample stock data - US Stocks
        us_stocks_data = [
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
        
        for stock_data in us_stocks_data:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults=stock_data
            )
            if created:
                self.stdout.write(f'Created US stock: {stock.symbol}')
            else:
                self.stdout.write(f'US stock {stock.symbol} already exists')

    def populate_pse_stocks(self):
        # Philippine Stock Exchange (PSE) stocks
        pse_stocks_data = [
            {
                'symbol': 'ACEN',
                'name': 'AC Energy Corporation',
                'exchange': 'PSE',
                'sector': 'Energy',
                'industry': 'Renewable Energy',
                'market_cap': 180000000000,  # ₱180B
                'currency': 'PHP',
                'current_price': Decimal('5.25'),
            },
            {
                'symbol': 'AGI',
                'name': 'Alliance Global Group Inc.',
                'exchange': 'PSE',
                'sector': 'Consumer Discretionary',
                'industry': 'Conglomerate',
                'market_cap': 200000000000,  # ₱200B
                'currency': 'PHP',
                'current_price': Decimal('12.50'),
            },
            {
                'symbol': 'ALI',
                'name': 'Ayala Land Inc.',
                'exchange': 'PSE',
                'sector': 'Real Estate',
                'industry': 'Real Estate Development',
                'market_cap': 350000000000,  # ₱350B
                'currency': 'PHP',
                'current_price': Decimal('28.75'),
            },
            {
                'symbol': 'BDO',
                'name': 'BDO Unibank Inc.',
                'exchange': 'PSE',
                'sector': 'Financial Services',
                'industry': 'Banking',
                'market_cap': 500000000000,  # ₱500B
                'currency': 'PHP',
                'current_price': Decimal('145.20'),
            },
            {
                'symbol': 'BPI',
                'name': 'Bank of the Philippine Islands',
                'exchange': 'PSE',
                'sector': 'Financial Services',
                'industry': 'Banking',
                'market_cap': 300000000000,  # ₱300B
                'currency': 'PHP',
                'current_price': Decimal('112.80'),
            },
            {
                'symbol': 'ICT',
                'name': 'International Container Terminal Services Inc.',
                'exchange': 'PSE',
                'sector': 'Industrials',
                'industry': 'Port Operations',
                'market_cap': 450000000000,  # ₱450B
                'currency': 'PHP',
                'current_price': Decimal('285.60'),
            },
            {
                'symbol': 'JFC',
                'name': 'Jollibee Foods Corporation',
                'exchange': 'PSE',
                'sector': 'Consumer Discretionary',
                'industry': 'Restaurants',
                'market_cap': 280000000000,  # ₱280B
                'currency': 'PHP',
                'current_price': Decimal('248.40'),
            },
            {
                'symbol': 'JGS',
                'name': 'John Gokongwei Jr. Holdings Inc.',
                'exchange': 'PSE',
                'sector': 'Consumer Staples',
                'industry': 'Conglomerate',
                'market_cap': 220000000000,  # ₱220B
                'currency': 'PHP',
                'current_price': Decimal('52.30'),
            },
            {
                'symbol': 'LTG',
                'name': 'LT Group Inc.',
                'exchange': 'PSE',
                'sector': 'Financial Services',
                'industry': 'Conglomerate',
                'market_cap': 150000000000,  # ₱150B
                'currency': 'PHP',
                'current_price': Decimal('9.85'),
            },
            {
                'symbol': 'MEG',
                'name': 'Megaworld Corporation',
                'exchange': 'PSE',
                'sector': 'Real Estate',
                'industry': 'Real Estate Development',
                'market_cap': 120000000000,  # ₱120B
                'currency': 'PHP',
                'current_price': Decimal('2.65'),
            },
            {
                'symbol': 'PLDT',
                'name': 'Philippine Long Distance Telephone Company',
                'exchange': 'PSE',
                'sector': 'Telecommunications',
                'industry': 'Telecommunications',
                'market_cap': 350000000000,  # ₱350B
                'currency': 'PHP',
                'current_price': Decimal('1620.00'),
            },
            {
                'symbol': 'SM',
                'name': 'SM Investments Corporation',
                'exchange': 'PSE',
                'sector': 'Consumer Discretionary',
                'industry': 'Retail/Real Estate',
                'market_cap': 600000000000,  # ₱600B
                'currency': 'PHP',
                'current_price': Decimal('890.00'),
            },
            {
                'symbol': 'SMC',
                'name': 'San Miguel Corporation',
                'exchange': 'PSE',
                'sector': 'Consumer Staples',
                'industry': 'Diversified',
                'market_cap': 400000000000,  # ₱400B
                'currency': 'PHP',
                'current_price': Decimal('120.50'),
            },
            {
                'symbol': 'TEL',
                'name': 'PLDT Inc.',
                'exchange': 'PSE',
                'sector': 'Telecommunications',
                'industry': 'Telecommunications',
                'market_cap': 320000000000,  # ₱320B
                'currency': 'PHP',
                'current_price': Decimal('1485.00'),
            },
            {
                'symbol': 'URC',
                'name': 'Universal Robina Corporation',
                'exchange': 'PSE',
                'sector': 'Consumer Staples',
                'industry': 'Food & Beverages',
                'market_cap': 250000000000,  # ₱250B
                'currency': 'PHP',
                'current_price': Decimal('112.60'),
            },
        ]
        
        for stock_data in pse_stocks_data:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults=stock_data
            )
            if created:
                self.stdout.write(f'Created PSE stock: {stock.symbol}')
            else:
                self.stdout.write(f'PSE stock {stock.symbol} already exists')

    def generate_historical_data(self):
        """Generate realistic historical price data for simulation"""
        stocks = Stock.objects.all()
        
        # Generate data for the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        for stock in stocks:
            current_price = float(stock.current_price) if stock.current_price else 100.0
            price = current_price * 0.9  # Start 10% lower than current
            
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends for realistic market simulation
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    # Generate realistic price movements
                    if stock.exchange == 'PSE':
                        # PSE stocks typically have smaller movements
                        change_percent = random.uniform(-0.05, 0.05)  # ±5%
                    else:
                        # US stocks can have larger movements
                        change_percent = random.uniform(-0.08, 0.08)  # ±8%
                    
                    price_change = price * change_percent
                    price = max(price + price_change, 0.01)  # Ensure price doesn't go negative
                    
                    # Create volume based on market cap
                    base_volume = min(stock.market_cap / 1000000, 1000000)  # Scale volume
                    volume = int(base_volume * random.uniform(0.5, 2.0))
                    
                    StockPrice.objects.get_or_create(
                        stock=stock,
                        date=current_date.date(),
                        defaults={
                            'open_price': Decimal(str(round(price * 0.999, 2))),
                            'high_price': Decimal(str(round(price * random.uniform(1.001, 1.03), 2))),
                            'low_price': Decimal(str(round(price * random.uniform(0.97, 0.999), 2))),
                            'close_price': Decimal(str(round(price, 2))),
                            'volume': volume,
                        }
                    )
                
                current_date += timedelta(days=1)
            
            # Update the stock's current price to the latest generated price
            stock.current_price = Decimal(str(round(price, 2)))
            stock.save()

        self.stdout.write(self.style.SUCCESS(f'Generated historical data for {stocks.count()} stocks'))