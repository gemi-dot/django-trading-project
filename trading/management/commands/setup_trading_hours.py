from django.core.management.base import BaseCommand
from django.utils import timezone
from trading.models import TradingHours, MarketHoliday
from datetime import time, date

class Command(BaseCommand):
    help = 'Populate trading hours for major stock exchanges'

    def handle(self, *args, **options):
        self.stdout.write('Creating trading hours for major exchanges...')
        
        # US Stock Exchanges (NYSE, NASDAQ)
        us_trading, created = TradingHours.objects.get_or_create(
            exchange='NYSE',
            defaults={
                'timezone': 'America/New_York',
                'market_open': time(9, 30),  # 9:30 AM
                'market_close': time(16, 0),  # 4:00 PM
                'premarket_open': time(4, 0),  # 4:00 AM
                'premarket_close': time(9, 30),  # 9:30 AM
                'afterhours_open': time(16, 0),  # 4:00 PM
                'afterhours_close': time(20, 0),  # 8:00 PM
                'monday_trading': True,
                'tuesday_trading': True,
                'wednesday_trading': True,
                'thursday_trading': True,
                'friday_trading': True,
                'saturday_trading': False,
                'sunday_trading': False,
            }
        )
        if created:
            self.stdout.write(f'✓ Created NYSE trading hours')
        else:
            self.stdout.write(f'✓ NYSE trading hours already exist')

        nasdaq_trading, created = TradingHours.objects.get_or_create(
            exchange='NASDAQ',
            defaults={
                'timezone': 'America/New_York',
                'market_open': time(9, 30),  # 9:30 AM
                'market_close': time(16, 0),  # 4:00 PM
                'premarket_open': time(4, 0),  # 4:00 AM
                'premarket_close': time(9, 30),  # 9:30 AM
                'afterhours_open': time(16, 0),  # 4:00 PM
                'afterhours_close': time(20, 0),  # 8:00 PM
                'monday_trading': True,
                'tuesday_trading': True,
                'wednesday_trading': True,
                'thursday_trading': True,
                'friday_trading': True,
                'saturday_trading': False,
                'sunday_trading': False,
            }
        )
        if created:
            self.stdout.write(f'✓ Created NASDAQ trading hours')
        else:
            self.stdout.write(f'✓ NASDAQ trading hours already exist')

        # Philippines Stock Exchange (PSE)
        pse_trading, created = TradingHours.objects.get_or_create(
            exchange='PSE',
            defaults={
                'timezone': 'Asia/Manila',
                'market_open': time(9, 30),  # 9:30 AM
                'market_close': time(15, 30),  # 3:30 PM
                'monday_trading': True,
                'tuesday_trading': True,
                'wednesday_trading': True,
                'thursday_trading': True,
                'friday_trading': True,
                'saturday_trading': False,
                'sunday_trading': False,
            }
        )
        if created:
            self.stdout.write(f'✓ Created PSE trading hours')
        else:
            self.stdout.write(f'✓ PSE trading hours already exist')

        # London Stock Exchange (LSE)
        lse_trading, created = TradingHours.objects.get_or_create(
            exchange='LSE',
            defaults={
                'timezone': 'Europe/London',
                'market_open': time(8, 0),  # 8:00 AM
                'market_close': time(16, 30),  # 4:30 PM
                'monday_trading': True,
                'tuesday_trading': True,
                'wednesday_trading': True,
                'thursday_trading': True,
                'friday_trading': True,
                'saturday_trading': False,
                'sunday_trading': False,
            }
        )
        if created:
            self.stdout.write(f'✓ Created LSE trading hours')
        else:
            self.stdout.write(f'✓ LSE trading hours already exist')

        # Tokyo Stock Exchange (TSE)
        tse_trading, created = TradingHours.objects.get_or_create(
            exchange='TSE',
            defaults={
                'timezone': 'Asia/Tokyo',
                'market_open': time(9, 0),  # 9:00 AM
                'market_close': time(15, 0),  # 3:00 PM (with lunch break 11:30-12:30)
                'monday_trading': True,
                'tuesday_trading': True,
                'wednesday_trading': True,
                'thursday_trading': True,
                'friday_trading': True,
                'saturday_trading': False,
                'sunday_trading': False,
            }
        )
        if created:
            self.stdout.write(f'✓ Created TSE trading hours')
        else:
            self.stdout.write(f'✓ TSE trading hours already exist')

        self.stdout.write('\n=== Creating 2025 US Market Holidays ===')
        
        # US Market Holidays for 2025
        us_holidays_2025 = [
            ('NYSE', 'New Year\'s Day', date(2025, 1, 1)),
            ('NYSE', 'Martin Luther King Jr. Day', date(2025, 1, 20)),
            ('NYSE', 'Washington\'s Birthday', date(2025, 2, 17)),
            ('NYSE', 'Good Friday', date(2025, 4, 18)),
            ('NYSE', 'Memorial Day', date(2025, 5, 26)),
            ('NYSE', 'Juneteenth', date(2025, 6, 19)),
            ('NYSE', 'Independence Day', date(2025, 7, 4)),
            ('NYSE', 'Labor Day', date(2025, 9, 1)),
            ('NYSE', 'Thanksgiving Day', date(2025, 11, 27)),
            ('NYSE', 'Christmas Day', date(2025, 12, 25)),
            
            ('NASDAQ', 'New Year\'s Day', date(2025, 1, 1)),
            ('NASDAQ', 'Martin Luther King Jr. Day', date(2025, 1, 20)),
            ('NASDAQ', 'Washington\'s Birthday', date(2025, 2, 17)),
            ('NASDAQ', 'Good Friday', date(2025, 4, 18)),
            ('NASDAQ', 'Memorial Day', date(2025, 5, 26)),
            ('NASDAQ', 'Juneteenth', date(2025, 6, 19)),
            ('NASDAQ', 'Independence Day', date(2025, 7, 4)),
            ('NASDAQ', 'Labor Day', date(2025, 9, 1)),
            ('NASDAQ', 'Thanksgiving Day', date(2025, 11, 27)),
            ('NASDAQ', 'Christmas Day', date(2025, 12, 25)),
        ]
        
        for exchange, name, holiday_date in us_holidays_2025:
            holiday, created = MarketHoliday.objects.get_or_create(
                exchange=exchange,
                date=holiday_date,
                defaults={
                    'name': name,
                    'is_partial_day': False,
                }
            )
            if created:
                self.stdout.write(f'✓ Added {exchange} holiday: {name} ({holiday_date})')

        # Early closing days for 2025
        early_close_days = [
            ('NYSE', 'Day after Thanksgiving', date(2025, 11, 28), time(13, 0)),  # 1:00 PM
            ('NYSE', 'Christmas Eve', date(2025, 12, 24), time(13, 0)),  # 1:00 PM
            ('NASDAQ', 'Day after Thanksgiving', date(2025, 11, 28), time(13, 0)),  # 1:00 PM
            ('NASDAQ', 'Christmas Eve', date(2025, 12, 24), time(13, 0)),  # 1:00 PM
        ]
        
        for exchange, name, holiday_date, early_close in early_close_days:
            holiday, created = MarketHoliday.objects.get_or_create(
                exchange=exchange,
                date=holiday_date,
                defaults={
                    'name': name,
                    'is_partial_day': True,
                    'early_close_time': early_close,
                    'notes': f'Market closes early at {early_close.strftime("%I:%M %p")}'
                }
            )
            if created:
                self.stdout.write(f'✓ Added {exchange} early close: {name} ({holiday_date}) - closes at {early_close.strftime("%I:%M %p")}')

        self.stdout.write('\n=== Philippines Stock Exchange Holidays ===')
        
        # PSE Holidays for 2025
        pse_holidays_2025 = [
            ('PSE', 'New Year\'s Day', date(2025, 1, 1)),
            ('PSE', 'People Power Anniversary', date(2025, 2, 25)),
            ('PSE', 'Maundy Thursday', date(2025, 4, 17)),
            ('PSE', 'Good Friday', date(2025, 4, 18)),
            ('PSE', 'Araw ng Kagitingan', date(2025, 4, 9)),
            ('PSE', 'Labor Day', date(2025, 5, 1)),
            ('PSE', 'Independence Day', date(2025, 6, 12)),
            ('PSE', 'National Heroes Day', date(2025, 8, 25)),
            ('PSE', 'Bonifacio Day', date(2025, 11, 30)),
            ('PSE', 'Rizal Day', date(2025, 12, 30)),
            ('PSE', 'New Year\'s Eve', date(2025, 12, 31)),
        ]
        
        for exchange, name, holiday_date in pse_holidays_2025:
            holiday, created = MarketHoliday.objects.get_or_create(
                exchange=exchange,
                date=holiday_date,
                defaults={
                    'name': name,
                    'is_partial_day': False,
                }
            )
            if created:
                self.stdout.write(f'✓ Added PSE holiday: {name} ({holiday_date})')

        self.stdout.write(self.style.SUCCESS('\n✅ Trading hours and holidays setup complete!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('• Check market status for any exchange')
        self.stdout.write('• Display trading hours in your templates')
        self.stdout.write('• Prevent trading during market holidays')
        self.stdout.write('• Show market open/close times in user timezone')