from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Stock, UserProfile, Portfolio, Trade, Watchlist, StockPrice, StopLossOrder, TechnicalIndicators, TradingHours, MarketHoliday

# Unregister the default User admin
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.register(User, UserAdmin)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'exchange', 'current_price', 'price_change_percent', 'volume', 'last_updated']
    list_filter = ['exchange', 'sector', 'industry', 'last_updated']
    search_fields = ['symbol', 'name', 'sector', 'industry']
    readonly_fields = ['last_updated', 'created_at']
    ordering = ['symbol']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('symbol', 'name', 'exchange', 'sector', 'industry')
        }),
        ('Market Data', {
            'fields': ('current_price', 'price_change', 'price_change_percent', 'volume', 'market_cap')
        }),
        ('Timestamps', {
            'fields': ('last_updated', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_balance', 'total_portfolio_value', 'risk_tolerance', 'experience_level']
    list_filter = ['risk_tolerance', 'experience_level', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Account Details', {
            'fields': ('account_balance', 'total_portfolio_value')
        }),
        ('Trading Profile', {
            'fields': ('risk_tolerance', 'experience_level')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'quantity', 'average_price', 'current_value', 'gain_loss_percent']
    list_filter = ['stock__exchange', 'stock__sector', 'created_at']
    search_fields = ['user__username', 'stock__symbol', 'stock__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'stock')

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'trade_type', 'order_type', 'quantity', 'price', 'stop_loss_price', 'total_amount', 'status', 'order_date']
    list_filter = ['trade_type', 'order_type', 'status', 'order_date', 'execution_date']
    search_fields = ['user__username', 'stock__symbol', 'stock__name']
    readonly_fields = ['order_date', 'total_amount']
    date_hierarchy = 'order_date'
    
    fieldsets = (
        ('Trade Information', {
            'fields': ('user', 'stock', 'trade_type', 'order_type', 'quantity', 'price')
        }),
        ('Stop Loss', {
            'fields': ('stop_loss_price',),
            'classes': ('collapse',)
        }),
        ('Order Details', {
            'fields': ('total_amount', 'commission', 'status', 'order_date', 'execution_date')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'stock')

@admin.register(StopLossOrder)
class StopLossOrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'quantity', 'stop_price', 'limit_price', 'status', 'created_at', 'triggered_at']
    list_filter = ['status', 'created_at', 'triggered_at']
    search_fields = ['user__username', 'stock__symbol', 'stock__name']
    readonly_fields = ['created_at', 'triggered_at', 'triggered_trade']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'stock', 'quantity', 'stop_price', 'limit_price')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Trigger Information', {
            'fields': ('triggered_at', 'triggered_trade'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'stock', 'triggered_trade')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'target_price', 'created_at']
    list_filter = ['stock__exchange', 'created_at']
    search_fields = ['user__username', 'stock__symbol', 'stock__name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'stock')

@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'close_price', 'volume', 'price_change_display']
    list_filter = ['stock__exchange', 'date']
    search_fields = ['stock__symbol', 'stock__name']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def price_change_display(self, obj):
        """Calculate daily price change for display"""
        if obj.open_price and obj.close_price:
            change = obj.close_price - obj.open_price
            change_percent = (change / obj.open_price) * 100 if obj.open_price else 0
            return f"{change:+.2f} ({change_percent:+.2f}%)"
        return "-"
    price_change_display.short_description = "Daily Change"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock')

@admin.register(TechnicalIndicators)
class TechnicalIndicatorsAdmin(admin.ModelAdmin):
    list_display = ['stock', 'trend_direction', 'trend_strength', 'overall_signal', 'signal_strength', 'rsi_14', 'last_updated']
    list_filter = ['trend_direction', 'overall_signal', 'last_updated']
    search_fields = ['stock__symbol', 'stock__name']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Stock Information', {
            'fields': ('stock',)
        }),
        ('Moving Averages', {
            'fields': ('sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26')
        }),
        ('Price Position Analysis', {
            'fields': ('price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200')
        }),
        ('Technical Indicators', {
            'fields': ('rsi_14', 'macd_line', 'macd_signal', 'macd_histogram')
        }),
        ('Bollinger Bands', {
            'fields': ('bb_upper', 'bb_middle', 'bb_lower', 'bb_width'),
            'classes': ('collapse',)
        }),
        ('Support & Resistance', {
            'fields': ('support_level', 'resistance_level'),
            'classes': ('collapse',)
        }),
        ('Volume Analysis', {
            'fields': ('volume_sma_20', 'volume_ratio'),
            'classes': ('collapse',)
        }),
        ('Trend & Signal Analysis', {
            'fields': ('trend_direction', 'trend_strength', 'overall_signal', 'signal_strength')
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock')

@admin.register(TradingHours)
class TradingHoursAdmin(admin.ModelAdmin):
    list_display = ['exchange', 'market_open', 'market_close', 'timezone']
    list_filter = ['exchange', 'timezone']
    fieldsets = [
        ('Exchange Information', {
            'fields': ['exchange', 'timezone']
        }),
        ('Regular Trading Hours', {
            'fields': ['market_open', 'market_close']
        }),
        ('Extended Hours', {
            'fields': ['premarket_open', 'premarket_close', 'afterhours_open', 'afterhours_close'],
            'classes': ['collapse']
        }),
        ('Trading Days', {
            'fields': ['monday_trading', 'tuesday_trading', 'wednesday_trading', 
                      'thursday_trading', 'friday_trading', 'saturday_trading', 'sunday_trading']
        }),
    ]

@admin.register(MarketHoliday)
class MarketHolidayAdmin(admin.ModelAdmin):
    list_display = ['exchange', 'name', 'date', 'is_partial_day', 'early_close_time']
    list_filter = ['exchange', 'date', 'is_partial_day']
    date_hierarchy = 'date'
    search_fields = ['name', 'exchange']

# Customize admin site header and title
admin.site.site_header = "Trading Platform Administration"
admin.site.site_title = "Trading Platform Admin"
admin.site.index_title = "Welcome to Trading Platform Administration"
