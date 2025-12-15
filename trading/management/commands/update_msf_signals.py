from django.core.management.base import BaseCommand
from trading.models import Stock, TechnicalIndicators
from decimal import Decimal
from datetime import datetime

class Command(BaseCommand):
    help = 'Update MSF technical indicators with current market signals'

    def handle(self, *args, **options):
        try:
            # Get or create MSF stock
            msf_stock, created = Stock.objects.get_or_create(
                symbol='MSF',
                defaults={
                    'name': 'Microsoft Corporation',
                    'exchange': 'NASDAQ',
                    'sector': 'Technology',
                    'industry': 'Software',
                    'current_price': Decimal('527.72')
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created MSF stock entry'))
            else:
                # Update current price
                msf_stock.current_price = Decimal('527.72')
                msf_stock.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Updated MSF current price to ${msf_stock.current_price}'))

            # Get or create technical indicators
            tech_indicators, created = TechnicalIndicators.objects.get_or_create(
                stock=msf_stock
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created new technical indicators for MSF'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✅ Updating existing technical indicators for MSF'))

            # Update with current MSF signals from your data
            tech_indicators.sma_20 = Decimal('483.06')
            tech_indicators.rsi_14 = Decimal('79.9')
            
            # Calculate actual price vs SMA20 percentage
            current_price = Decimal('527.72')
            sma_20 = Decimal('483.06')
            price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100
            tech_indicators.price_vs_sma20 = price_vs_sma20
            
            # Set volume ratio (0.7x vs average)
            tech_indicators.volume_ratio = Decimal('0.7')
            
            # Based on RSI 79.9 (overbought) but price well above SMA20
            # RSI overbought suggests potential pullback, but trend is still up
            tech_indicators.trend_direction = 'bullish'  # Price 9.2% above SMA20
            tech_indicators.trend_strength = Decimal('70.0')  # Strong but RSI warning
            
            # RSI overbought suggests caution - recommend HOLD
            tech_indicators.overall_signal = 'hold'  # Overbought condition
            tech_indicators.signal_strength = Decimal('75.0')  # Strong signal due to clear overbought
            
            # Set support and resistance levels based on recent price action
            tech_indicators.support_level = Decimal('502.01')  # Recent low from Dec 8
            tech_indicators.resistance_level = Decimal('533.30')  # Recent high from Dec 12
            
            tech_indicators.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎯 Successfully updated MSF technical indicators:\n'
                    f'  📈 Current Price: ${msf_stock.current_price}\n'
                    f'  📊 SMA 20: ${tech_indicators.sma_20}\n'
                    f'  📉 RSI 14: {tech_indicators.rsi_14} (OVERBOUGHT)\n'
                    f'  💹 Price vs SMA20: +{tech_indicators.price_vs_sma20:.1f}%\n'
                    f'  📦 Volume Ratio: {tech_indicators.volume_ratio}x vs average\n'
                    f'  🎯 Overall Signal: {tech_indicators.overall_signal.upper()}\n'
                    f'  💪 Signal Strength: {tech_indicators.signal_strength}%\n'
                    f'  🔻 Support: ${tech_indicators.support_level}\n'
                    f'  🔺 Resistance: ${tech_indicators.resistance_level}\n'
                    f'\n📝 Analysis: Price is {tech_indicators.price_vs_sma20:.1f}% above SMA20 (bullish)\n'
                    f'     but RSI at {tech_indicators.rsi_14} indicates overbought conditions.\n'
                    f'     Recommendation: HOLD and watch for pullback to support levels.'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating MSF signals: {str(e)}')
            )