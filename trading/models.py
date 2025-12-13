from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
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
