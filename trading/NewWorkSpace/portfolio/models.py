from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def total_value(self):
        positions_value = sum(pos.current_value for pos in self.positions.all())
        return self.cash_balance + positions_value


class Asset(models.Model):
    ASSET_TYPES = [
        ('STOCK', 'Stock'),
        ('ETF', 'ETF'),
        ('CRYPTO', 'Cryptocurrency'),
        ('FOREX', 'Forex'),
        ('COMMODITY', 'Commodity'),
    ]
    
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    exchange = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Position(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=15, decimal_places=8)
    average_cost = models.DecimalField(max_digits=15, decimal_places=8)
    current_price = models.DecimalField(max_digits=15, decimal_places=8, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('portfolio', 'asset')

    def __str__(self):
        return f"{self.portfolio.name} - {self.asset.symbol}: {self.quantity}"

    @property
    def current_value(self):
        return self.quantity * self.current_price

    @property
    def total_cost(self):
        return self.quantity * self.average_cost

    @property
    def unrealized_pnl(self):
        return self.current_value - self.total_cost

    @property
    def unrealized_pnl_percent(self):
        if self.total_cost > 0:
            return (self.unrealized_pnl / self.total_cost) * 100
        return 0


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('DEPOSIT', 'Cash Deposit'),
        ('WITHDRAWAL', 'Cash Withdrawal'),
        ('DIVIDEND', 'Dividend'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=8, null=True, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=8, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        if self.asset:
            return f"{self.transaction_type} {self.quantity} {self.asset.symbol} at ${self.price}"
        return f"{self.transaction_type} ${self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Calculate total_amount for buy/sell transactions
        if self.transaction_type in ['BUY', 'SELL'] and self.quantity and self.price:
            self.total_amount = self.quantity * self.price + self.fees
        super().save(*args, **kwargs)
