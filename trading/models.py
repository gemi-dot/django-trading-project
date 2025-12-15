from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Stock(models.Model):
    """Model representing a stock/security"""
    symbol = models.CharField(max_length=10, unique=True, help_text="Stock ticker symbol (e.g., AAPL)")
    name = models.CharField(max_length=200, help_text="Full company name")
    exchange = models.CharField(max_length=50, help_text="Stock exchange (e.g., NASDAQ, NYSE)")
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    market_cap = models.BigIntegerField(null=True, blank=True, help_text="Market capitalization in USD")
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_change_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True, help_text="Trading volume")
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name}"

class UserProfile(models.Model):
    """Extended user profile for trading-specific information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trading_profile')
    account_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_portfolio_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[
            ('conservative', 'Conservative'),
            ('moderate', 'Moderate'),
            ('aggressive', 'Aggressive'),
        ],
        default='moderate'
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Trading Profile"

class Portfolio(models.Model):
    """User's stock portfolio"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    gain_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    gain_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['-current_value']

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} ({self.quantity} shares)"

class Trade(models.Model):
    """Model representing individual trades"""
    TRADE_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled'),
        ('partial', 'Partially Filled'),
        ('stop_loss_triggered', 'Stop Loss Triggered'),
    ]

    ORDER_TYPES = [
        ('market', 'Market Order'),
        ('limit', 'Limit Order'),
        ('stop_loss', 'Stop Loss'),
        ('stop_limit', 'Stop Limit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    order_type = models.CharField(max_length=15, choices=ORDER_TYPES, default='market')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stop_loss_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    execution_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.trade_type.upper()} {self.quantity} {self.stock.symbol} @ ${self.price}"

    def save(self, *args, **kwargs):
        # Calculate total amount if not provided
        if not self.total_amount:
            self.total_amount = self.quantity * self.price + self.commission
        super().save(*args, **kwargs)

class StopLossOrder(models.Model):
    """Model for active stop-loss orders"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('triggered', 'Triggered'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stop_loss_orders')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    stop_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at which to trigger the stop loss")
    limit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                      help_text="Limit price for stop-limit orders")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    triggered_trade = models.ForeignKey(Trade, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Stop Loss: {self.stock.symbol} @ ${self.stop_price} ({self.quantity} shares)"

class Watchlist(models.Model):
    """User's stock watchlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    target_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['stock__symbol']

    def __str__(self):
        return f"{self.user.username}'s watchlist - {self.stock.symbol}"

class StockPrice(models.Model):
    """Historical stock price data"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='price_history')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    adjusted_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ['stock', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.stock.symbol} - {self.date} - ${self.close_price}"

class TechnicalIndicators(models.Model):
    """Model for storing technical analysis indicators"""
    stock = models.OneToOneField(Stock, on_delete=models.CASCADE, related_name='technical_indicators')
    
    # Moving Averages
    sma_20 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="20-day Simple Moving Average")
    sma_50 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="50-day Simple Moving Average")
    sma_200 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="200-day Simple Moving Average")
    ema_12 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="12-day Exponential Moving Average")
    ema_26 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="26-day Exponential Moving Average")
    ema_200 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="200-day Exponential Moving Average")
    
    # Moving Average Directions (trend direction for each MA)
    DIRECTION_CHOICES = [
        ('up', 'Upward'),
        ('down', 'Downward'),
        ('sideways', 'Sideways'),
    ]
    
    ema_200_direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, null=True, blank=True, help_text="200 EMA trend direction")
    sma_200_direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, null=True, blank=True, help_text="200 SMA trend direction")
    
    # MACD (Moving Average Convergence Divergence)
    macd_line = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    macd_histogram = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # RSI (Relative Strength Index)
    rsi_14 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="14-day RSI")
    
    # Bollinger Bands
    bb_upper = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    bb_middle = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    bb_lower = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    bb_width = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Trend Analysis
    TREND_CHOICES = [
        ('strong_bullish', 'Strong Bullish'),
        ('bullish', 'Bullish'),
        ('neutral', 'Neutral'),
        ('bearish', 'Bearish'),
        ('strong_bearish', 'Strong Bearish'),
    ]
    
    trend_direction = models.CharField(max_length=20, choices=TREND_CHOICES, default='neutral')
    trend_strength = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Trend strength 0-100")
    
    # Price Position Analysis
    price_vs_sma20 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="% above/below SMA20")
    price_vs_sma50 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="% above/below SMA50")
    price_vs_sma200 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="% above/below SMA200")
    
    # Support and Resistance
    support_level = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    resistance_level = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Volume Analysis
    volume_sma_20 = models.BigIntegerField(null=True, blank=True, help_text="20-day average volume")
    volume_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Current volume vs average")
    
    # Overall Signal
    SIGNAL_CHOICES = [
        ('strong_buy', 'Strong Buy'),
        ('buy', 'Buy'),
        ('hold', 'Hold'),
        ('sell', 'Sell'),
        ('strong_sell', 'Strong Sell'),
    ]
    
    overall_signal = models.CharField(max_length=15, choices=SIGNAL_CHOICES, default='hold')
    signal_strength = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Signal confidence 0-100")
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Technical Indicators"
        verbose_name_plural = "Technical Indicators"
    
    def __str__(self):
        return f"{self.stock.symbol} - Technical Analysis"
    
    def get_trend_color(self):
        """Return Bootstrap color class for trend"""
        colors = {
            'strong_bullish': 'success',
            'bullish': 'success',
            'neutral': 'secondary',
            'bearish': 'danger',
            'strong_bearish': 'danger'
        }
        return colors.get(self.trend_direction, 'secondary')
    
    def get_signal_color(self):
        """Return Bootstrap color class for signal"""
        colors = {
            'strong_buy': 'success',
            'buy': 'success',
            'hold': 'warning',
            'sell': 'danger',
            'strong_sell': 'danger'
        }
        return colors.get(self.overall_signal, 'warning')

class TradingPerformance(models.Model):
    """Track user's trading performance for learning and analysis"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trading_performance')
    
    # Overall Performance Metrics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    total_profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_fees_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Performance Ratios
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Percentage of winning trades")
    average_win = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_loss = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_factor = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Gross profit / Gross loss")
    
    # Best and Worst Trades
    best_trade_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    worst_trade_loss = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Trading Behavior Metrics
    average_holding_period_days = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    most_traded_symbol = models.CharField(max_length=10, blank=True, null=True)
    favorite_trading_time = models.CharField(max_length=20, blank=True, null=True)
    
    # Learning Progress
    SKILL_LEVEL_CHOICES = [
        ('novice', 'Novice'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    estimated_skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default='novice')
    trading_days_active = models.IntegerField(default=0)
    longest_winning_streak = models.IntegerField(default=0)
    longest_losing_streak = models.IntegerField(default=0)
    
    # Risk Management Metrics
    largest_position_size = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    risk_per_trade_avg = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Average % of account risked per trade")
    stop_loss_usage_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="% of trades with stop loss")
    
    # Simulation Specific
    simulation_start_date = models.DateTimeField(auto_now_add=True)
    last_trade_date = models.DateTimeField(null=True, blank=True)
    peak_account_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'))
    max_drawdown = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trading Performance"
        verbose_name_plural = "Trading Performance"
    
    def __str__(self):
        return f"{self.user.username}'s Trading Performance"
    
    def update_performance_metrics(self):
        """Calculate and update performance metrics based on completed trades"""
        completed_trades = Trade.objects.filter(
            user=self.user,
            status='executed'
        ).order_by('execution_date')
        
        if not completed_trades.exists():
            return
        
        self.total_trades = completed_trades.count()
        
        # Calculate wins/losses
        winning_trades = []
        losing_trades = []
        total_profit = Decimal('0.00')
        total_loss = Decimal('0.00')
        total_fees = Decimal('0.00')
        
        for trade in completed_trades:
            total_fees += trade.commission
            
            if trade.trade_type == 'sell':
                # Calculate P&L for sell trades
                # This is simplified - in reality you'd need to match with corresponding buy trades
                profit_loss = (trade.price - trade.stock.current_price) * trade.quantity
                if profit_loss > 0:
                    winning_trades.append(trade)
                    total_profit += profit_loss
                else:
                    losing_trades.append(trade)
                    total_loss += abs(profit_loss)
        
        self.winning_trades = len(winning_trades)
        self.losing_trades = len(losing_trades)
        self.total_fees_paid = total_fees
        
        # Calculate ratios
        if self.total_trades > 0:
            self.win_rate = Decimal(str(self.winning_trades / self.total_trades * 100))
        
        if self.winning_trades > 0:
            self.average_win = total_profit / self.winning_trades
        
        if self.losing_trades > 0:
            self.average_loss = total_loss / self.losing_trades
        
        if total_loss > 0:
            self.profit_factor = total_profit / total_loss
        
        self.total_profit_loss = total_profit - total_loss
        
        # Update last trade date
        if completed_trades.exists():
            self.last_trade_date = completed_trades.last().execution_date
        
        self.save()
    
    def get_performance_grade(self):
        """Return a letter grade based on performance"""
        if self.total_trades < 10:
            return 'N/A'  # Not enough data
        
        score = 0
        
        # Win rate (40% of score)
        if self.win_rate >= 60:
            score += 40
        elif self.win_rate >= 50:
            score += 30
        elif self.win_rate >= 40:
            score += 20
        else:
            score += 10
        
        # Profit factor (30% of score)
        if self.profit_factor >= 2.0:
            score += 30
        elif self.profit_factor >= 1.5:
            score += 25
        elif self.profit_factor >= 1.0:
            score += 15
        else:
            score += 5
        
        # Risk management (30% of score)
        if self.stop_loss_usage_rate >= 80:
            score += 30
        elif self.stop_loss_usage_rate >= 60:
            score += 20
        elif self.stop_loss_usage_rate >= 40:
            score += 10
        
        # Convert to letter grade
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 65:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

class TradingHours(models.Model):
    """Model for managing trading hours for different exchanges"""
    exchange = models.CharField(max_length=50, unique=True, help_text="Exchange name (e.g., NYSE, NASDAQ, PSE)")
    timezone = models.CharField(max_length=50, default='America/New_York', help_text="Exchange timezone")
    
    # Regular trading hours
    market_open = models.TimeField(help_text="Market opening time")
    market_close = models.TimeField(help_text="Market closing time")
    
    # Pre-market hours (optional)
    premarket_open = models.TimeField(null=True, blank=True, help_text="Pre-market opening time")
    premarket_close = models.TimeField(null=True, blank=True, help_text="Pre-market closing time")
    
    # After-hours trading (optional)
    afterhours_open = models.TimeField(null=True, blank=True, help_text="After-hours opening time")
    afterhours_close = models.TimeField(null=True, blank=True, help_text="After-hours closing time")
    
    # Trading days (Monday=0, Sunday=6)
    monday_trading = models.BooleanField(default=True)
    tuesday_trading = models.BooleanField(default=True)
    wednesday_trading = models.BooleanField(default=True)
    thursday_trading = models.BooleanField(default=True)
    friday_trading = models.BooleanField(default=True)
    saturday_trading = models.BooleanField(default=False)
    sunday_trading = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trading Hours"
        verbose_name_plural = "Trading Hours"
        ordering = ['exchange']
    
    def __str__(self):
        return f"{self.exchange} Trading Hours"
    
    def is_trading_day(self, date=None):
        """Check if given date (or today) is a trading day"""
        from django.utils import timezone
        if date is None:
            date = timezone.now().date()
        
        weekday = date.weekday()  # Monday=0, Sunday=6
        trading_days = [
            self.monday_trading,
            self.tuesday_trading,
            self.wednesday_trading,
            self.thursday_trading,
            self.friday_trading,
            self.saturday_trading,
            self.sunday_trading,
        ]
        return trading_days[weekday]
    
    def is_market_open(self, datetime_obj=None):
        """Check if market is currently open"""
        from django.utils import timezone
        import pytz
        
        if datetime_obj is None:
            datetime_obj = timezone.now()
        
        # Convert to exchange timezone
        exchange_tz = pytz.timezone(self.timezone)
        local_time = datetime_obj.astimezone(exchange_tz)
        
        # Check for holidays first
        holiday = MarketHoliday.objects.filter(
            exchange=self.exchange,
            date=local_time.date()
        ).first()
        
        if holiday:
            if holiday.is_partial_day and holiday.early_close_time:
                # Handle partial trading day
                current_time = local_time.time()
                if self.market_open <= current_time <= holiday.early_close_time:
                    return True, f"Market open - Early close at {holiday.early_close_time.strftime('%I:%M %p')} ({holiday.name})"
                else:
                    return False, f"Market closed - {holiday.name} (Early close at {holiday.early_close_time.strftime('%I:%M %p')})"
            else:
                return False, f"Market closed - {holiday.name}"
        
        # Check if it's a trading day
        if not self.is_trading_day(local_time.date()):
            return False, "Market closed - Non-trading day"
        
        current_time = local_time.time()
        
        # Check regular trading hours
        if self.market_open <= current_time <= self.market_close:
            return True, "Market open - Regular hours"
        
        # Check pre-market hours
        if self.premarket_open and current_time >= self.premarket_open and current_time < self.market_open:
            return True, "Pre-market trading"
        
        # Check after-hours trading
        if self.afterhours_close and current_time > self.market_close and current_time <= self.afterhours_close:
            return True, "After-hours trading"
        
        # Market is closed - provide next opening info
        if current_time < self.market_open:
            if self.premarket_open and current_time < self.premarket_open:
                return False, f"Market opens at {self.premarket_open.strftime('%I:%M %p')} (Pre-market)"
            else:
                return False, f"Market opens at {self.market_open.strftime('%I:%M %p')}"
        else:
            return False, f"Market closed at {self.market_close.strftime('%I:%M %p')}"
    
    def get_market_status(self, datetime_obj=None):
        """Get detailed market status information"""
        from django.utils import timezone
        import pytz
        
        if datetime_obj is None:
            datetime_obj = timezone.now()
        
        exchange_tz = pytz.timezone(self.timezone)
        local_time = datetime_obj.astimezone(exchange_tz)
        
        is_open, status_message = self.is_market_open(datetime_obj)
        
        return {
            'is_open': is_open,
            'status_message': status_message,
            'local_time': local_time,
            'exchange_timezone': self.timezone,
            'is_trading_day': self.is_trading_day(local_time.date()),
            'market_open': self.market_open,
            'market_close': self.market_close,
            'premarket_open': self.premarket_open,
            'afterhours_close': self.afterhours_close,
        }

class MarketHoliday(models.Model):
    """Model for market holidays when exchanges are closed"""
    exchange = models.CharField(max_length=50, help_text="Exchange name")
    name = models.CharField(max_length=100, help_text="Holiday name")
    date = models.DateField(help_text="Holiday date")
    is_partial_day = models.BooleanField(default=False, help_text="Half-day trading")
    early_close_time = models.TimeField(null=True, blank=True, help_text="Early closing time for partial days")
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['exchange', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.exchange} - {self.name} ({self.date})"

class TradingLesson(models.Model):
    """Educational content for learning trading concepts"""
    LESSON_CATEGORIES = [
        ('basics', 'Trading Basics'),
        ('technical', 'Technical Analysis'),
        ('fundamental', 'Fundamental Analysis'),
        ('risk_management', 'Risk Management'),
        ('psychology', 'Trading Psychology'),
        ('strategies', 'Trading Strategies'),
        ('market_types', 'Market Types'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=LESSON_CATEGORIES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    content = models.TextField(help_text="Lesson content in markdown format")
    key_concepts = models.JSONField(default=list, help_text="List of key concepts covered")
    estimated_read_time = models.IntegerField(help_text="Estimated reading time in minutes")
    order_index = models.IntegerField(default=0, help_text="Order within category")
    
    # Prerequisites and recommendations
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='unlocks')
    recommended_practice = models.TextField(blank=True, help_text="Recommended practice exercises")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order_index']
        unique_together = ['category', 'order_index']
    
    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

class UserLessonProgress(models.Model):
    """Track user progress through trading lessons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(TradingLesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"

class PullbackStrategy(models.Model):
    """Model for AAPL Pullback Strategy Configuration"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pullback_strategies')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    
    # Strategy Parameters
    trend_timeframe = models.CharField(max_length=20, default='daily', help_text="Timeframe for trend analysis")
    entry_timeframe = models.CharField(max_length=20, default='1hour', help_text="Timeframe for entry signals")
    risk_per_trade = models.DecimalField(max_digits=5, decimal_places=2, default=0.5, help_text="Risk percentage per trade")
    max_trades_per_day = models.IntegerField(default=1, help_text="Maximum trades allowed per day")
    
    # Pullback Configuration
    pullback_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=2.0, help_text="Minimum pullback % from high")
    sma_period = models.IntegerField(default=20, help_text="SMA period for trend confirmation")
    volume_confirmation = models.BooleanField(default=True, help_text="Require volume confirmation")
    
    # Risk Management
    stop_loss_atr_multiple = models.DecimalField(max_digits=5, decimal_places=2, default=2.0, help_text="Stop loss as ATR multiple")
    take_profit_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=2.0, help_text="Risk:Reward ratio")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} Pullback Strategy"

class PullbackTrade(models.Model):
    """Model for tracking pullback strategy trades"""
    TRADE_STATUS = [
        ('setup', 'Setup Identified'),
        ('waiting_entry', 'Waiting for Entry'),
        ('entered', 'Position Entered'),
        ('stop_hit', 'Stop Loss Hit'),
        ('target_hit', 'Take Profit Hit'),
        ('manual_exit', 'Manual Exit'),
        ('expired', 'Setup Expired'),
    ]
    
    ENTRY_REASON = [
        ('pullback_bounce', 'Pullback Bounce off SMA'),
        ('volume_confirmation', 'Volume Confirmation'),
        ('hammer_candle', 'Hammer Candle Pattern'),
        ('support_bounce', 'Support Level Bounce'),
        ('oversold_bounce', 'Oversold RSI Bounce'),
    ]
    
    strategy = models.ForeignKey(PullbackStrategy, on_delete=models.CASCADE, related_name='trades')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    
    # Setup Details
    setup_date = models.DateTimeField()
    trend_direction = models.CharField(max_length=20, default='bullish')
    pullback_high = models.DecimalField(max_digits=10, decimal_places=2, help_text="High before pullback")
    pullback_low = models.DecimalField(max_digits=10, decimal_places=2, help_text="Low of pullback")
    pullback_percentage_actual = models.DecimalField(max_digits=5, decimal_places=2, help_text="Actual pullback %")
    
    # Entry Details
    entry_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    entry_date = models.DateTimeField(null=True, blank=True)
    entry_reason = models.CharField(max_length=30, choices=ENTRY_REASON, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    
    # Risk Management
    stop_loss_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    take_profit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    risk_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Exit Details
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exit_date = models.DateTimeField(null=True, blank=True)
    pnl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pnl_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=TRADE_STATUS, default='setup')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-setup_date']
    
    def __str__(self):
        return f"Pullback Trade: {self.stock.symbol} - {self.status}"

class PullbackAnalysis(models.Model):
    """Real-time analysis for AAPL pullback opportunities"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    analysis_date = models.DateTimeField()
    
    # Trend Analysis (Daily TF)
    daily_trend = models.CharField(max_length=20)
    price_vs_sma20 = models.DecimalField(max_digits=5, decimal_places=2)
    sma20_slope = models.CharField(max_length=10, help_text="rising/falling/flat")
    volume_trend = models.CharField(max_length=20)
    
    # Current Market State
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    distance_from_high = models.DecimalField(max_digits=5, decimal_places=2, help_text="% from recent high")
    is_pullback_valid = models.BooleanField(default=False)
    
    # 1-Hour Analysis
    hourly_support_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_resistance_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rsi_1h = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    volume_spike = models.BooleanField(default=False)
    
    # 5-Minute Check
    five_min_momentum = models.CharField(max_length=20)
    entry_signal_strength = models.IntegerField(default=0, help_text="0-10 signal strength")
    
    # Recommendations
    action_recommended = models.CharField(max_length=30)
    confidence_level = models.IntegerField(default=0, help_text="0-100 confidence")
    risk_assessment = models.CharField(max_length=20)
    
    class Meta:
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"AAPL Analysis - {self.analysis_date.strftime('%Y-%m-%d %H:%M')}"

class TradingLog(models.Model):
    """Comprehensive logging for pullback strategy"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('trade', 'Trade'),
        ('analysis', 'Analysis'),
        ('signal', 'Signal'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    stock_symbol = models.CharField(max_length=10, null=True, blank=True)
    trade_id = models.IntegerField(null=True, blank=True)
    price_data = models.JSONField(null=True, blank=True, help_text="JSON data for prices, indicators, etc.")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.level.upper()} - {self.timestamp.strftime('%H:%M:%S')} - {self.message[:50]}"

class DailyTradingSession(models.Model):
    """Track daily trading sessions and performance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Session Stats
    trades_taken = models.IntegerField(default=0)
    max_trades_allowed = models.IntegerField(default=1)
    total_risk_taken = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # P&L Tracking
    realized_pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unrealized_pnl = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Market Conditions
    market_condition = models.CharField(max_length=30, null=True, blank=True)
    aapl_daily_range = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    volume_vs_average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Session Notes
    pre_market_analysis = models.TextField(blank=True, null=True)
    post_session_review = models.TextField(blank=True, null=True)
    lessons_learned = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.trades_taken} trades"

class PreMarketStopLoss(models.Model):
    """Model for stop-loss orders that can be set before market open"""
    STATUS_CHOICES = [
        ('pending', 'Pending Market Open'),
        ('active', 'Active'),
        ('triggered', 'Triggered'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    ORDER_TYPES = [
        ('stop_loss', 'Stop Loss'),
        ('trailing_stop', 'Trailing Stop'),
        ('stop_limit', 'Stop Limit'),
    ]
    
    TRIGGER_CONDITIONS = [
        ('market_open', 'Trigger at Market Open'),
        ('pre_market', 'Trigger in Pre-Market'),
        ('any_session', 'Trigger Any Trading Session'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='premarket_stop_losses')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    
    # Order Details
    order_type = models.CharField(max_length=15, choices=ORDER_TYPES, default='stop_loss')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    stop_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at which to trigger the stop loss")
    limit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                      help_text="Limit price for stop-limit orders")
    
    # Trailing Stop Settings
    trail_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                       help_text="Fixed dollar amount for trailing stop")
    trail_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                        help_text="Percentage for trailing stop")
    
    # Execution Settings
    trigger_condition = models.CharField(max_length=15, choices=TRIGGER_CONDITIONS, default='market_open')
    good_till_cancelled = models.BooleanField(default=True, help_text="Order remains active until cancelled")
    expiry_date = models.DateField(null=True, blank=True, help_text="Order expires after this date")
    
    # Market Session Preferences
    execute_in_premarket = models.BooleanField(default=False, help_text="Allow execution in pre-market hours")
    execute_in_afterhours = models.BooleanField(default=False, help_text="Allow execution in after-hours")
    
    # Risk Management
    max_slippage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.5'), 
                                               help_text="Maximum acceptable slippage percentage")
    min_volume_threshold = models.IntegerField(default=1000, help_text="Minimum volume required for execution")
    
    # Order Tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True, help_text="When order became active")
    triggered_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Execution Details
    executed_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    executed_quantity = models.IntegerField(null=True, blank=True)
    slippage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    execution_session = models.CharField(max_length=20, null=True, blank=True, 
                                         help_text="pre-market, regular, after-hours")
    
    # Related Orders and Trades
    related_trade = models.ForeignKey(Trade, on_delete=models.SET_NULL, null=True, blank=True)
    parent_order = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                     help_text="For linked orders like OCO")
    
    # Notes and Strategy
    strategy_name = models.CharField(max_length=100, blank=True, help_text="Trading strategy this order is part of")
    notes = models.TextField(blank=True)
    alert_settings = models.JSONField(default=dict, help_text="Email/SMS alert preferences")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pre-Market Stop Loss"
        verbose_name_plural = "Pre-Market Stop Losses"
    
    def __str__(self):
        return f"Pre-Market {self.get_order_type_display()}: {self.stock.symbol} @ ${self.stop_price} ({self.get_status_display()})"
    
    def activate_at_market_open(self):
        """Activate the order when market opens"""
        if self.status == 'pending' and self.trigger_condition == 'market_open':
            self.status = 'active'
            self.activated_at = timezone.now()
            self.save()
            return True
        return False
    
    def check_trigger_condition(self, current_price, session_type='regular'):
        """Check if stop loss should be triggered"""
        if self.status != 'active':
            return False
        
        # Check session permissions
        if session_type == 'pre-market' and not self.execute_in_premarket:
            return False
        if session_type == 'after-hours' and not self.execute_in_afterhours:
            return False
        
        # Check if stop price is hit
        if self.order_type == 'trailing_stop':
            return self._check_trailing_stop(current_price)
        else:
            return current_price <= self.stop_price
    
    def _check_trailing_stop(self, current_price):
        """Logic for trailing stop orders"""
        if not self.trail_amount and not self.trail_percent:
            return False
        
        # Get the highest price since order was activated
        # This would need to be tracked in a separate model or calculated
        # For now, simplified logic
        if self.trail_percent:
            trail_price = current_price * (1 - self.trail_percent / 100)
            return current_price <= trail_price
        elif self.trail_amount:
            trail_price = current_price - self.trail_amount
            return current_price <= trail_price
        
        return False
    
    def execute_order(self, execution_price, session_type='regular'):
        """Execute the stop loss order"""
        from django.utils import timezone
        
        if self.status != 'active':
            return False, "Order is not active"
        
        # Calculate slippage
        expected_price = self.stop_price
        slippage_amount = abs(execution_price - expected_price)
        slippage_percent = (slippage_amount / expected_price) * 100
        
        # Check slippage tolerance
        if slippage_percent > self.max_slippage_percent:
            return False, f"Slippage too high: {slippage_percent:.2f}%"
        
        # Create the actual trade
        trade = Trade.objects.create(
            user=self.user,
            stock=self.stock,
            trade_type='sell',
            order_type='stop_loss',
            quantity=self.quantity,
            price=execution_price,
            total_amount=self.quantity * execution_price,
            status='executed',
            execution_date=timezone.now(),
            notes=f"Stop loss triggered from pre-market order {self.id}"
        )
        
        # Update order status
        self.status = 'triggered'
        self.triggered_at = timezone.now()
        self.executed_at = timezone.now()
        self.executed_price = execution_price
        self.executed_quantity = self.quantity
        self.slippage = slippage_amount
        self.execution_session = session_type
        self.related_trade = trade
        self.save()
        
        return True, f"Stop loss executed at ${execution_price}"
    
    def cancel_order(self, reason="User cancelled"):
        """Cancel the order"""
        from django.utils import timezone
        
        if self.status in ['pending', 'active']:
            self.status = 'cancelled'
            self.notes += f"\nCancelled: {reason} at {timezone.now()}"
            self.save()
            return True
        return False
    
    def get_estimated_execution_price(self):
        """Get estimated execution price based on current market conditions"""
        if self.order_type == 'stop_limit' and self.limit_price:
            return min(self.stop_price, self.limit_price)
        return self.stop_price

class PreMarketWatchlist(models.Model):
    """Enhanced watchlist for pre-market monitoring and stop-loss setup"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='premarket_watchlists')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    
    # Pre-market specific settings
    monitor_premarket = models.BooleanField(default=True, help_text="Monitor during pre-market hours")
    premarket_alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                     help_text="Alert if price moves this % in pre-market")
    
    # Stop-loss preparation
    auto_create_stop_loss = models.BooleanField(default=False, help_text="Auto-create stop loss at market open")
    default_stop_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                     help_text="Default stop loss percentage below entry")
    target_entry_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    planned_position_size = models.IntegerField(null=True, blank=True, help_text="Planned number of shares")
    
    # Risk management preferences
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                         help_text="Maximum acceptable loss for this stock today")
    risk_reward_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.0'),
                                            help_text="Target risk:reward ratio")
    
    # Market session preferences
    trade_premarket = models.BooleanField(default=False)
    trade_regular_hours = models.BooleanField(default=True)
    trade_afterhours = models.BooleanField(default=False)
    
    # Alerts and notifications
    email_alerts = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'stock']
        ordering = ['stock__symbol']
        verbose_name = "Pre-Market Watchlist"
        verbose_name_plural = "Pre-Market Watchlists"
    
    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} (Pre-Market Watch)"
    
    def create_stop_loss_at_open(self, entry_price):
        """Create stop loss order when market opens"""
        if not self.auto_create_stop_loss or not self.default_stop_loss_percent:
            return None
        
        stop_price = entry_price * (1 - self.default_stop_loss_percent / 100)
        
        stop_loss = PreMarketStopLoss.objects.create(
            user=self.user,
            stock=self.stock,
            order_type='stop_loss',
            quantity=self.planned_position_size or 100,
            stop_price=stop_price,
            trigger_condition='market_open',
            strategy_name='Auto-created from watchlist',
            notes=f"Auto-created stop loss from watchlist settings"
        )
        
        return stop_loss

class SkillAssessment(models.Model):
    """Comprehensive skill assessment and rating system"""
    SKILL_CATEGORIES = [
        ('technical_analysis', 'Technical Analysis'),
        ('fundamental_analysis', 'Fundamental Analysis'),
        ('risk_management', 'Risk Management'),
        ('market_psychology', 'Market Psychology'),
        ('position_sizing', 'Position Sizing'),
        ('entry_timing', 'Entry Timing'),
        ('exit_strategy', 'Exit Strategy'),
        ('portfolio_management', 'Portfolio Management'),
        ('options_trading', 'Options Trading'),
        ('sector_analysis', 'Sector Analysis'),
    ]
    
    PROFICIENCY_LEVELS = [
        (0, 'No Experience'),
        (1, 'Novice (0-3 months)'),
        (2, 'Beginner (3-6 months)'),
        (3, 'Developing (6-12 months)'),
        (4, 'Intermediate (1-2 years)'),
        (5, 'Competent (2-3 years)'),
        (6, 'Proficient (3-5 years)'),
        (7, 'Advanced (5+ years)'),
        (8, 'Expert (Professional level)'),
        (9, 'Master (Teaching level)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_assessments')
    category = models.CharField(max_length=30, choices=SKILL_CATEGORIES)
    
    # Current Skill Level (0-9)
    current_level = models.IntegerField(choices=PROFICIENCY_LEVELS, default=0)
    target_level = models.IntegerField(choices=PROFICIENCY_LEVELS, default=4)
    
    # Detailed Scoring (0-100)
    knowledge_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Theoretical knowledge")
    practical_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Practical application")
    consistency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Consistent application")
    
    # Overall Assessment
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Weighted average")
    confidence_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Self-assessed confidence 0-10")
    
    # Progress Tracking
    last_assessment_date = models.DateTimeField(auto_now=True)
    next_review_date = models.DateField(null=True, blank=True)
    improvement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Points gained per month")
    
    # Practice Recommendations
    recommended_practice_hours_weekly = models.IntegerField(default=5)
    focus_areas = models.JSONField(default=list, help_text="Specific areas to focus on")
    
    class Meta:
        unique_together = ['user', 'category']
        ordering = ['-overall_score']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()}: Level {self.current_level}"
    
    def calculate_overall_score(self):
        """Calculate weighted overall score"""
        # 40% knowledge, 35% practical, 25% consistency
        self.overall_score = (
            self.knowledge_score * 0.4 + 
            self.practical_score * 0.35 + 
            self.consistency_score * 0.25
        )
        self.save()
        return self.overall_score
    
    def get_skill_grade(self):
        """Return letter grade based on overall score"""
        if self.overall_score >= 95: return 'A+'
        elif self.overall_score >= 90: return 'A'
        elif self.overall_score >= 85: return 'A-'
        elif self.overall_score >= 80: return 'B+'
        elif self.overall_score >= 75: return 'B'
        elif self.overall_score >= 70: return 'B-'
        elif self.overall_score >= 65: return 'C+'
        elif self.overall_score >= 60: return 'C'
        elif self.overall_score >= 55: return 'C-'
        else: return 'F'
    
    def recommend_next_steps(self):
        """Generate personalized learning recommendations"""
        recommendations = []
        
        if self.knowledge_score < 70:
            recommendations.append({
                'type': 'study',
                'priority': 'high',
                'action': f'Complete {self.get_category_display()} theory lessons',
                'time_estimate': '2-3 hours'
            })
        
        if self.practical_score < self.knowledge_score - 10:
            recommendations.append({
                'type': 'practice',
                'priority': 'high', 
                'action': 'Practice with simulated trades',
                'time_estimate': '1-2 hours daily'
            })
        
        if self.consistency_score < 60:
            recommendations.append({
                'type': 'habit',
                'priority': 'medium',
                'action': 'Create daily trading routine checklist',
                'time_estimate': '30 minutes setup'
            })
        
        return recommendations

class PracticeModule(models.Model):
    """Interactive practice modules for skill development"""
    MODULE_TYPES = [
        ('simulation', 'Trading Simulation'),
        ('quiz', 'Knowledge Quiz'),
        ('case_study', 'Case Study Analysis'),
        ('pattern_recognition', 'Chart Pattern Recognition'),
        ('risk_calculator', 'Risk Management Calculator'),
        ('backtesting', 'Strategy Backtesting'),
        ('market_replay', 'Historical Market Replay'),
        ('options_strategy', 'Options Strategy Builder'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    module_type = models.CharField(max_length=20, choices=MODULE_TYPES)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS)
    
    # Skill targeting
    target_skills = models.ManyToManyField('SkillAssessment', blank=True, related_name='practice_modules')
    required_level = models.IntegerField(default=1, help_text="Minimum skill level required")
    
    # Module Configuration
    estimated_duration = models.IntegerField(help_text="Duration in minutes")
    max_attempts = models.IntegerField(default=3, help_text="Maximum attempts allowed")
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    
    # Content and Data
    content_data = models.JSONField(help_text="Module configuration and content")
    scoring_rules = models.JSONField(help_text="How performance is scored")
    
    # Tracking
    completion_count = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['difficulty', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

class UserPracticeSession(models.Model):
    """Track individual practice sessions"""
    SESSION_STATUS = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_sessions')
    module = models.ForeignKey(PracticeModule, on_delete=models.CASCADE, related_name='sessions')
    
    # Session Tracking
    status = models.CharField(max_length=15, choices=SESSION_STATUS, default='started')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Performance Metrics
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    speed_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Detailed Results
    answers = models.JSONField(default=dict, help_text="User answers and choices")
    performance_data = models.JSONField(default=dict, help_text="Detailed performance metrics")
    
    # Learning Insights
    strengths_identified = models.JSONField(default=list)
    weaknesses_identified = models.JSONField(default=list)
    recommended_focus = models.TextField(blank=True)
    
    attempt_number = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title} (Attempt {self.attempt_number})"
    
    def calculate_skill_improvement(self):
        """Calculate how much this session improved user's skills"""
        improvements = {}
        
        if self.status == 'completed' and self.score >= self.module.passing_score:
            # Calculate improvement based on performance
            base_improvement = min(self.score / 100 * 5, 5)  # Max 5 points
            
            # Bonus for high accuracy and speed
            if self.accuracy > 90:
                base_improvement *= 1.2
            if self.speed_score > 80:
                base_improvement *= 1.1
            
            improvements['points'] = round(base_improvement, 2)
            improvements['areas'] = self.strengths_identified
            
        return improvements

class LearningPath(models.Model):
    """Structured learning paths for different trading goals"""
    PATH_TYPES = [
        ('beginner_complete', 'Complete Beginner Program'),
        ('day_trader', 'Day Trading Mastery'),
        ('swing_trader', 'Swing Trading Expert'),
        ('options_trader', 'Options Trading Specialist'),
        ('technical_analyst', 'Technical Analysis Master'),
        ('risk_manager', 'Risk Management Expert'),
        ('portfolio_manager', 'Portfolio Management Pro'),
    ]
    
    name = models.CharField(max_length=200)
    path_type = models.CharField(max_length=30, choices=PATH_TYPES)
    description = models.TextField()
    
    # Path Configuration
    estimated_duration_weeks = models.IntegerField(help_text="Estimated completion time")
    difficulty_progression = models.CharField(max_length=50, default="Beginner to Advanced")
    prerequisite_skills = models.JSONField(default=list, help_text="Required starting skills")
    
    # Content Structure
    lessons = models.ManyToManyField(TradingLesson, through='PathLesson', related_name='learning_paths')
    practice_modules = models.ManyToManyField(PracticeModule, through='PathPractice', related_name='learning_paths')
    
    # Outcomes
    target_skills = models.JSONField(default=list, help_text="Skills developed upon completion")
    completion_certificate = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['path_type']
    
    def __str__(self):
        return f"{self.name} ({self.estimated_duration_weeks} weeks)"

class PathLesson(models.Model):
    """Through model for lessons in learning paths"""
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    lesson = models.ForeignKey(TradingLesson, on_delete=models.CASCADE)
    order_index = models.IntegerField()
    is_required = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order_index']
        unique_together = ['path', 'order_index']

class PathPractice(models.Model):
    """Through model for practice modules in learning paths"""
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    module = models.ForeignKey(PracticeModule, on_delete=models.CASCADE)
    order_index = models.IntegerField()
    unlock_after_lesson = models.ForeignKey(TradingLesson, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['order_index']

class UserLearningProgress(models.Model):
    """Track user progress through learning paths"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_progress')
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    
    # Progress Tracking
    started_at = models.DateTimeField(auto_now_add=True)
    current_lesson_index = models.IntegerField(default=0)
    current_practice_index = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Performance
    overall_grade = models.CharField(max_length=3, blank=True)
    lessons_completed = models.IntegerField(default=0)
    practices_completed = models.IntegerField(default=0)
    average_practice_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'path']
    
    def __str__(self):
        return f"{self.user.username} - {self.path.name} ({self.completion_percentage}%)"

class TradingChallenge(models.Model):
    """Weekly/Monthly trading challenges for skill practice"""
    CHALLENGE_TYPES = [
        ('weekly_performance', 'Weekly Performance Challenge'),
        ('risk_management', 'Risk Management Challenge'),
        ('pattern_trading', 'Pattern Recognition Challenge'),
        ('sector_rotation', 'Sector Rotation Challenge'),
        ('earnings_play', 'Earnings Season Challenge'),
        ('volatility_trading', 'Volatility Trading Challenge'),
        ('paper_trading', 'Paper Trading Competition'),
    ]
    
    CHALLENGE_DURATION = [
        ('daily', 'Daily Challenge'),
        ('weekly', 'Weekly Challenge'),
        ('monthly', 'Monthly Challenge'),
        ('quarterly', 'Quarterly Challenge'),
    ]
    
    title = models.CharField(max_length=200)
    challenge_type = models.CharField(max_length=30, choices=CHALLENGE_TYPES)
    duration = models.CharField(max_length=15, choices=CHALLENGE_DURATION)
    
    # Challenge Configuration
    description = models.TextField()
    rules = models.JSONField(help_text="Challenge rules and constraints")
    success_criteria = models.JSONField(help_text="What constitutes success")
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    # Participation
    max_participants = models.IntegerField(default=100)
    entry_requirements = models.JSONField(default=dict, help_text="Skill level or other requirements")
    
    # Rewards and Recognition
    prizes = models.JSONField(default=list, help_text="Prizes for top performers")
    skill_points_reward = models.IntegerField(default=0, help_text="Skill points for participation")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_duration_display()})"

class ChallengeParticipation(models.Model):
    """Track user participation in challenges"""
    PARTICIPATION_STATUS = [
        ('registered', 'Registered'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('disqualified', 'Disqualified'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_participations')
    challenge = models.ForeignKey(TradingChallenge, on_delete=models.CASCADE, related_name='participants')
    
    # Participation Tracking
    status = models.CharField(max_length=15, choices=PARTICIPATION_STATUS, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Performance Metrics
    current_score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_rank = models.IntegerField(null=True, blank=True)
    performance_data = models.JSONField(default=dict, help_text="Detailed performance tracking")
    
    # Final Results
    final_score = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_rank = models.IntegerField(null=True, blank=True)
    achieved_goals = models.JSONField(default=list, help_text="Goals achieved during challenge")
    
    class Meta:
        unique_together = ['user', 'challenge']
        ordering = ['-final_score']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"

class SkillBadge(models.Model):
    """Achievement badges for various trading skills and milestones"""
    BADGE_CATEGORIES = [
        ('knowledge', 'Knowledge Mastery'),
        ('performance', 'Trading Performance'),
        ('consistency', 'Consistency Achievement'),
        ('risk_management', 'Risk Management'),
        ('learning', 'Learning Progress'),
        ('community', 'Community Contribution'),
        ('challenge', 'Challenge Achievement'),
    ]
    
    BADGE_TIERS = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=BADGE_CATEGORIES)
    tier = models.CharField(max_length=10, choices=BADGE_TIERS)
    
    # Badge Details
    description = models.TextField()
    requirements = models.JSONField(help_text="Requirements to earn this badge")
    icon_url = models.CharField(max_length=200, blank=True)
    
    # Rewards
    skill_points = models.IntegerField(default=0, help_text="Skill points awarded")
    unlocks = models.JSONField(default=list, help_text="What this badge unlocks")
    
    # Tracking
    total_earned = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category', 'tier']
        unique_together = ['name', 'tier']
    
    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"

class UserBadge(models.Model):
    """Track badges earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(SkillBadge, on_delete=models.CASCADE, related_name='earned_by')
    
    earned_at = models.DateTimeField(auto_now_add=True)
    progress_data = models.JSONField(default=dict, help_text="Progress data when badge was earned")
    
    # Display Settings
    is_displayed = models.BooleanField(default=True, help_text="Show on profile")
    display_order = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"
