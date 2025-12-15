from django.db import models
from django.utils import timezone


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    exchange = models.CharField(max_length=50)
    sector = models.CharField(max_length=100, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    class Meta:
        ordering = ['symbol']


class PriceData(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='price_data')
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    adjusted_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['stock', 'timestamp']
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.timestamp.date()}: ${self.close_price}"


class TechnicalIndicator(models.Model):
    INDICATOR_TYPES = [
        ('SMA', 'Simple Moving Average'),
        ('EMA', 'Exponential Moving Average'),
        ('RSI', 'Relative Strength Index'),
        ('MACD', 'Moving Average Convergence Divergence'),
        ('BB', 'Bollinger Bands'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='indicators')
    indicator_type = models.CharField(max_length=10, choices=INDICATOR_TYPES)
    period = models.IntegerField()
    timestamp = models.DateTimeField()
    value = models.DecimalField(max_digits=15, decimal_places=6)
    additional_data = models.JSONField(null=True, blank=True)  # For complex indicators like MACD
    
    class Meta:
        unique_together = ['stock', 'indicator_type', 'period', 'timestamp']
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.stock.symbol} {self.indicator_type}({self.period}) - {self.value}"
