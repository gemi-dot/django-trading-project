from django.core.management.base import BaseCommand
from decimal import Decimal
import statistics
from datetime import date, timedelta
from trading.models import Stock, StockPrice, TechnicalIndicators

class Command(BaseCommand):
    help = 'Calculate and update technical indicators for all stocks'

    def handle(self, *args, **options):
        stocks = Stock.objects.all()
        
        for stock in stocks:
            self.stdout.write(f'Calculating technical indicators for {stock.symbol}...')
            
            # Get historical price data (last 200 days for calculations)
            price_data = StockPrice.objects.filter(
                stock=stock
            ).order_by('-date')[:200]
            
            if len(price_data) < 20:  # Need at least 20 days for basic calculations
                self.stdout.write(f'  Skipping {stock.symbol} - insufficient price data')
                continue
            
            # Convert to lists for easier calculation (reverse to get chronological order)
            price_data = list(reversed(price_data))
            closes = [float(p.close_price) for p in price_data]
            volumes = [p.volume for p in price_data]
            highs = [float(p.high_price) for p in price_data]
            lows = [float(p.low_price) for p in price_data]
            
            # Get or create technical indicators record
            tech_indicators, created = TechnicalIndicators.objects.get_or_create(
                stock=stock
            )
            
            # Calculate Moving Averages
            if len(closes) >= 20:
                tech_indicators.sma_20 = Decimal(str(statistics.mean(closes[-20:])))
                tech_indicators.price_vs_sma20 = self.calculate_price_position(stock.current_price, tech_indicators.sma_20)
            
            if len(closes) >= 50:
                tech_indicators.sma_50 = Decimal(str(statistics.mean(closes[-50:])))
                tech_indicators.price_vs_sma50 = self.calculate_price_position(stock.current_price, tech_indicators.sma_50)
            
            if len(closes) >= 200:
                tech_indicators.sma_200 = Decimal(str(statistics.mean(closes[-200:])))
                tech_indicators.price_vs_sma200 = self.calculate_price_position(stock.current_price, tech_indicators.sma_200)
            
            # Calculate EMAs
            if len(closes) >= 12:
                tech_indicators.ema_12 = self.calculate_ema(closes, 12)
            if len(closes) >= 26:
                tech_indicators.ema_26 = self.calculate_ema(closes, 26)
            
            # Calculate 200 EMA and its direction
            if len(closes) >= 200:
                current_ema_200 = self.calculate_ema(closes, 200)
                previous_ema_200 = None
                
                # Calculate previous EMA 200 if we have enough data
                if len(closes) > 200:
                    previous_ema_200 = self.calculate_ema(closes[:-1], 200)
                
                tech_indicators.ema_200 = current_ema_200
                
                # Determine EMA 200 direction
                if previous_ema_200:
                    if current_ema_200 > previous_ema_200:
                        tech_indicators.ema_200_direction = 'up'
                    elif current_ema_200 < previous_ema_200:
                        tech_indicators.ema_200_direction = 'down'
                    else:
                        tech_indicators.ema_200_direction = 'sideways'
                else:
                    # For first calculation, compare with SMA 200 if available
                    if tech_indicators.sma_200:
                        if current_ema_200 > tech_indicators.sma_200:
                            tech_indicators.ema_200_direction = 'up'
                        elif current_ema_200 < tech_indicators.sma_200:
                            tech_indicators.ema_200_direction = 'down'
                        else:
                            tech_indicators.ema_200_direction = 'sideways'
                    else:
                        tech_indicators.ema_200_direction = 'neutral'
                
                # Calculate price position relative to EMA 200
                if stock.current_price and tech_indicators.ema_200:
                    tech_indicators.price_vs_ema200 = ((stock.current_price - tech_indicators.ema_200) / tech_indicators.ema_200) * 100
            
            # Calculate MACD
            if tech_indicators.ema_12 and tech_indicators.ema_26:
                tech_indicators.macd_line = tech_indicators.ema_12 - tech_indicators.ema_26
                # Simplified MACD signal (normally would use EMA of MACD line)
                if len(closes) >= 35:
                    macd_values = []
                    for i in range(max(26, len(closes) - 9), len(closes)):
                        if i >= 26:
                            ema12_val = self.calculate_ema(closes[:i], 12)
                            ema26_val = self.calculate_ema(closes[:i], 26)
                            macd_values.append(float(ema12_val - ema26_val))
                    
                    if macd_values:
                        tech_indicators.macd_signal = Decimal(str(statistics.mean(macd_values[-9:])))
                        tech_indicators.macd_histogram = tech_indicators.macd_line - tech_indicators.macd_signal
            
            # Calculate RSI
            if len(closes) >= 15:
                tech_indicators.rsi_14 = self.calculate_rsi(closes, 14)
            
            # Calculate Bollinger Bands
            if len(closes) >= 20:
                bb_period = 20
                sma = statistics.mean(closes[-bb_period:])
                std_dev = statistics.stdev(closes[-bb_period:])
                tech_indicators.bb_middle = Decimal(str(sma))
                tech_indicators.bb_upper = Decimal(str(sma + (2 * std_dev)))
                tech_indicators.bb_lower = Decimal(str(sma - (2 * std_dev)))
                tech_indicators.bb_width = tech_indicators.bb_upper - tech_indicators.bb_lower
            
            # Calculate Support and Resistance levels
            if len(lows) >= 20 and len(highs) >= 20:
                recent_lows = lows[-20:]
                recent_highs = highs[-20:]
                tech_indicators.support_level = Decimal(str(min(recent_lows)))
                tech_indicators.resistance_level = Decimal(str(max(recent_highs)))
            
            # Calculate Volume indicators
            if len(volumes) >= 20:
                tech_indicators.volume_sma_20 = int(statistics.mean(volumes[-20:]))
                if stock.volume and tech_indicators.volume_sma_20 > 0:
                    tech_indicators.volume_ratio = Decimal(str(stock.volume / tech_indicators.volume_sma_20))
            
            # Determine Trend Direction and Strength
            trend_data = self.analyze_trend(closes, tech_indicators)
            tech_indicators.trend_direction = trend_data['direction']
            tech_indicators.trend_strength = trend_data['strength']
            
            # Calculate Overall Signal
            signal_data = self.calculate_overall_signal(tech_indicators, stock)
            tech_indicators.overall_signal = signal_data['signal']
            tech_indicators.signal_strength = signal_data['strength']
            
            tech_indicators.save()
            
            self.stdout.write(f'  ✓ Updated {stock.symbol} - Trend: {tech_indicators.trend_direction}, Signal: {tech_indicators.overall_signal}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully calculated technical indicators for {len(stocks)} stocks')
        )
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return Decimal('0')
        
        multiplier = 2 / (period + 1)
        ema = statistics.mean(prices[:period])  # Start with SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return Decimal(str(ema))
    
    def calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return Decimal('50')
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return Decimal('50')
        
        avg_gain = statistics.mean(gains[-period:])
        avg_loss = statistics.mean(losses[-period:])
        
        if avg_loss == 0:
            return Decimal('100')
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return Decimal(str(rsi))
    
    def calculate_price_position(self, current_price, moving_average):
        """Calculate percentage position relative to moving average"""
        if not current_price or not moving_average or moving_average == 0:
            return Decimal('0')
        
        position = ((current_price - moving_average) / moving_average) * 100
        return Decimal(str(position))
    
    def analyze_trend(self, closes, tech_indicators):
        """Analyze trend direction and strength"""
        if len(closes) < 20:
            return {'direction': 'neutral', 'strength': Decimal('0')}
        
        # Simple trend analysis based on moving averages and price action
        current_price = closes[-1]
        trend_score = 0
        
        # Check moving average relationships
        if tech_indicators.sma_20 and tech_indicators.sma_50:
            if tech_indicators.sma_20 > tech_indicators.sma_50:
                trend_score += 1
            else:
                trend_score -= 1
        
        if tech_indicators.sma_50 and tech_indicators.sma_200:
            if tech_indicators.sma_50 > tech_indicators.sma_200:
                trend_score += 1
            else:
                trend_score -= 1
        
        # Check price vs moving averages
        if tech_indicators.sma_20:
            if current_price > float(tech_indicators.sma_20):
                trend_score += 1
            else:
                trend_score -= 1
        
        # Check recent price momentum
        if len(closes) >= 5:
            recent_change = (closes[-1] - closes[-5]) / closes[-5] * 100
            if recent_change > 2:
                trend_score += 1
            elif recent_change < -2:
                trend_score -= 1
        
        # Determine trend direction
        if trend_score >= 3:
            direction = 'strong_bullish'
            strength = min(100, abs(trend_score) * 20)
        elif trend_score >= 1:
            direction = 'bullish'
            strength = abs(trend_score) * 15
        elif trend_score <= -3:
            direction = 'strong_bearish'
            strength = min(100, abs(trend_score) * 20)
        elif trend_score <= -1:
            direction = 'bearish'
            strength = abs(trend_score) * 15
        else:
            direction = 'neutral'
            strength = 0
        
        return {
            'direction': direction,
            'strength': Decimal(str(strength))
        }
    
    def calculate_overall_signal(self, tech_indicators, stock):
        """Calculate overall buy/sell signal based on multiple indicators"""
        signal_score = 0
        
        # RSI analysis
        if tech_indicators.rsi_14:
            rsi = float(tech_indicators.rsi_14)
            if rsi < 30:  # Oversold
                signal_score += 2
            elif rsi < 40:
                signal_score += 1
            elif rsi > 70:  # Overbought
                signal_score -= 2
            elif rsi > 60:
                signal_score -= 1
        
        # MACD analysis
        if tech_indicators.macd_line and tech_indicators.macd_signal:
            if tech_indicators.macd_line > tech_indicators.macd_signal:
                signal_score += 1
            else:
                signal_score -= 1
        
        # Trend analysis
        if tech_indicators.trend_direction in ['strong_bullish', 'bullish']:
            signal_score += 2 if 'strong' in tech_indicators.trend_direction else 1
        elif tech_indicators.trend_direction in ['strong_bearish', 'bearish']:
            signal_score -= 2 if 'strong' in tech_indicators.trend_direction else 1
        
        # Price position analysis
        if tech_indicators.price_vs_sma20:
            price_pos = float(tech_indicators.price_vs_sma20)
            if price_pos > 5:  # Well above SMA20
                signal_score += 1
            elif price_pos < -5:  # Well below SMA20
                signal_score -= 1
        
        # Determine signal
        if signal_score >= 4:
            signal = 'strong_buy'
            strength = min(100, abs(signal_score) * 15)
        elif signal_score >= 2:
            signal = 'buy'
            strength = abs(signal_score) * 12
        elif signal_score <= -4:
            signal = 'strong_sell'
            strength = min(100, abs(signal_score) * 15)
        elif signal_score <= -2:
            signal = 'sell'
            strength = abs(signal_score) * 12
        else:
            signal = 'hold'
            strength = 50 + (abs(signal_score) * 5)
        
        return {
            'signal': signal,
            'strength': Decimal(str(strength))
        }