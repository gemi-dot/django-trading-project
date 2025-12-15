from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from market_data.models import Stock
from portfolio.models import Portfolio


class TradingStrategy(models.Model):
    STRATEGY_TYPES = [
        ('MOMENTUM', 'Momentum Strategy'),
        ('MEAN_REVERSION', 'Mean Reversion'),
        ('BREAKOUT', 'Breakout Strategy'),
        ('PAIRS_TRADING', 'Pairs Trading'),
        ('TECHNICAL', 'Technical Analysis'),
        ('FUNDAMENTAL', 'Fundamental Analysis'),
        ('CUSTOM', 'Custom Strategy'),
    ]
    
    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('VERY_HIGH', 'Very High Risk'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    strategy_type = models.CharField(max_length=20, choices=STRATEGY_TYPES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Strategy parameters stored as JSON
    parameters = models.JSONField(default=dict)
    
    # Performance metrics
    total_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.strategy_type})"
    
    class Meta:
        verbose_name_plural = "Trading Strategies"


class Signal(models.Model):
    SIGNAL_TYPES = [
        ('BUY', 'Buy Signal'),
        ('SELL', 'Sell Signal'),
        ('HOLD', 'Hold Signal'),
        ('STRONG_BUY', 'Strong Buy'),
        ('STRONG_SELL', 'Strong Sell'),
    ]
    
    SIGNAL_STATUS = [
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE, related_name='signals')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    signal_type = models.CharField(max_length=12, choices=SIGNAL_TYPES)
    status = models.CharField(max_length=10, choices=SIGNAL_STATUS, default='PENDING')
    
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    volume_recommendation = models.IntegerField(null=True, blank=True)
    
    # Additional signal data
    signal_data = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.signal_type} {self.stock.symbol} at ${self.target_price}"
    
    class Meta:
        ordering = ['-generated_at']


class Backtest(models.Model):
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE, related_name='backtests')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField()
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Results
    final_capital = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_return_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    annual_return_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    volatility = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    max_drawdown_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    
    # Trade statistics
    total_trades = models.IntegerField(null=True, blank=True)
    winning_trades = models.IntegerField(null=True, blank=True)
    losing_trades = models.IntegerField(null=True, blank=True)
    win_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Store detailed results as JSON
    detailed_results = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Backtest: {self.name} ({self.strategy.name})"


class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    TRADE_STATUS = [
        ('PENDING', 'Pending'),
        ('FILLED', 'Filled'),
        ('PARTIAL', 'Partially Filled'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='trades')
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.SET_NULL, null=True, blank=True)
    signal = models.ForeignKey(Signal, on_delete=models.SET_NULL, null=True, blank=True)
    backtest = models.ForeignKey(Backtest, on_delete=models.SET_NULL, null=True, blank=True)
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    status = models.CharField(max_length=10, choices=TRADE_STATUS, default='PENDING')
    
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Fees and costs
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Order details
    order_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.trade_type} {self.quantity} {self.stock.symbol} at ${self.price}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(str(self.quantity)) * self.price
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class StrategyPerformance(models.Model):
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    
    # Daily performance metrics
    daily_return = models.DecimalField(max_digits=8, decimal_places=4)
    cumulative_return = models.DecimalField(max_digits=10, decimal_places=4)
    portfolio_value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Risk metrics
    volatility = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    beta = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['strategy', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.strategy.name} - {self.date}: {self.daily_return}%"
