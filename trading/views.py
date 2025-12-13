from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import ListView, DetailView
from decimal import Decimal
from .models import (Stock, Portfolio, Trade, Watchlist, UserProfile, StockPrice, StopLossOrder, 
                    TradingLesson, UserLessonProgress, TradingPerformance)

def home(request):
    """Home page view"""
    context = {
        'total_stocks': Stock.objects.count(),
        'recent_stocks': Stock.objects.order_by('-last_updated')[:5],
    }
    return render(request, 'trading/home.html', context)

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile automatically
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to the trading platform.')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    context = {'form': form}
    return render(request, 'registration/signup.html', context)

@login_required
def dashboard(request):
    """User dashboard with portfolio overview"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's portfolio
    portfolio_items = Portfolio.objects.filter(user=request.user).select_related('stock')
    
    # Calculate portfolio statistics
    total_portfolio_value = portfolio_items.aggregate(
        total_value=Sum(F('quantity') * F('stock__current_price'))
    )['total_value'] or Decimal('0.00')
    
    total_invested = portfolio_items.aggregate(
        total_invested=Sum(F('quantity') * F('average_price'))
    )['total_invested'] or Decimal('0.00')
    
    total_gain_loss = total_portfolio_value - total_invested
    gain_loss_percent = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    # Update user profile with latest portfolio value
    user_profile.total_portfolio_value = total_portfolio_value
    user_profile.save()
    
    # Recent trades
    recent_trades = Trade.objects.filter(user=request.user).select_related('stock').order_by('-order_date')[:5]
    
    # Watchlist items
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('stock')[:5]
    
    context = {
        'user_profile': user_profile,
        'portfolio_items': portfolio_items,
        'total_portfolio_value': total_portfolio_value,
        'total_invested': total_invested,
        'total_gain_loss': total_gain_loss,
        'gain_loss_percent': gain_loss_percent,
        'recent_trades': recent_trades,
        'watchlist_items': watchlist_items,
    }
    return render(request, 'trading/dashboard.html', context)

@login_required
def learning_dashboard(request):
    """Main learning dashboard with lessons and progress"""
    # Get all lessons organized by category
    lessons_by_category = {}
    for lesson in TradingLesson.objects.all().order_by('category', 'order_index'):
        if lesson.category not in lessons_by_category:
            lessons_by_category[lesson.category] = []
        
        # Check if user has progress on this lesson
        try:
            progress = UserLessonProgress.objects.get(user=request.user, lesson=lesson)
            lesson.user_progress = progress
        except UserLessonProgress.DoesNotExist:
            lesson.user_progress = None
            
        lessons_by_category[lesson.category].append(lesson)
    
    # Get user's overall learning stats
    total_lessons = TradingLesson.objects.count()
    completed_lessons = UserLessonProgress.objects.filter(
        user=request.user, 
        completed=True
    ).count()
    
    # Get user's trading performance
    try:
        performance = TradingPerformance.objects.get(user=request.user)
    except TradingPerformance.DoesNotExist:
        # Create initial performance record
        performance = TradingPerformance.objects.create(
            user=request.user,
            total_trades=Trade.objects.filter(user=request.user).count()
        )
    
    # Update performance stats
    trades = Trade.objects.filter(user=request.user, status='executed')
    if trades.exists():
        performance.total_trades = trades.count()
        profitable_trades = trades.filter(
            trade_type='sell',
            total_amount__gt=F('quantity') * F('stock__current_price')
        ).count()
        performance.profitable_trades = profitable_trades
        performance.win_rate = (profitable_trades / trades.count()) * 100 if trades.count() > 0 else 0
        performance.save()
    
    context = {
        'lessons_by_category': lessons_by_category,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'completion_percentage': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
        'performance': performance,
    }
    return render(request, 'trading/learning_dashboard.html', context)

@login_required
def lesson_detail(request, lesson_id):
    """Display a specific trading lesson"""
    lesson = get_object_or_404(TradingLesson, id=lesson_id)
    
    # Get or create user progress for this lesson
    progress, created = UserLessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'started_at': timezone.now()}
    )
    
    # Mark as completed if user clicks complete button
    if request.method == 'POST' and request.POST.get('action') == 'complete':
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.save()
            messages.success(request, f'Congratulations! You completed "{lesson.title}"')
        return redirect('lesson_detail', lesson_id=lesson.id)
    
    # Get next and previous lessons
    next_lesson = TradingLesson.objects.filter(
        category=lesson.category,
        order_index__gt=lesson.order_index
    ).order_by('order_index').first()
    
    prev_lesson = TradingLesson.objects.filter(
        category=lesson.category,
        order_index__lt=lesson.order_index
    ).order_by('-order_index').first()
    
    context = {
        'lesson': lesson,
        'progress': progress,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
    }
    return render(request, 'trading/lesson_detail.html', context)

@login_required
def trading_performance(request):
    """Detailed trading performance analytics"""
    # Get or create performance record
    performance, created = TradingPerformance.objects.get_or_create(
        user=request.user,
        defaults={'total_trades': 0}
    )
    
    # Get all user's trades
    trades = Trade.objects.filter(
        user=request.user, 
        status='executed'
    ).select_related('stock').order_by('-execution_date')
    
    # Calculate detailed statistics
    buy_trades = trades.filter(trade_type='buy')
    sell_trades = trades.filter(trade_type='sell')
    
    total_invested = buy_trades.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_received = sell_trades.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate current portfolio value
    portfolio_value = Portfolio.objects.filter(user=request.user).aggregate(
        total=Sum(F('quantity') * F('stock__current_price'))
    )['total'] or 0
    
    # Recent trading activity (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_trades = trades.filter(execution_date__gte=thirty_days_ago)
    
    # Monthly performance
    monthly_stats = []
    for i in range(6):  # Last 6 months
        month_start = (timezone.now() - timezone.timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
        
        month_trades = trades.filter(
            execution_date__gte=month_start,
            execution_date__lte=month_end
        )
        
        monthly_stats.append({
            'month': month_start.strftime('%B %Y'),
            'trades': month_trades.count(),
            'volume': month_trades.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        })
    
    # Update performance record
    performance.total_trades = trades.count()
    performance.total_profit_loss = total_received - total_invested + portfolio_value
    performance.save()
    
    context = {
        'performance': performance,
        'trades': trades[:20],  # Latest 20 trades
        'buy_trades_count': buy_trades.count(),
        'sell_trades_count': sell_trades.count(),
        'total_invested': total_invested,
        'total_received': total_received,
        'portfolio_value': portfolio_value,
        'recent_trades_count': recent_trades.count(),
        'monthly_stats': monthly_stats,
    }
    return render(request, 'trading/trading_performance.html', context)

class StockListView(ListView):
    """List all stocks with search and filter functionality"""
    model = Stock
    template_name = 'trading/stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Stock.objects.all()
        
        # Search functionality
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(symbol__icontains=query) |
                Q(name__icontains=query) |
                Q(sector__icontains=query)
            )
        
        # Filter by exchange
        exchange = self.request.GET.get('exchange')
        if exchange:
            queryset = queryset.filter(exchange=exchange)
        
        # Filter by sector
        sector = self.request.GET.get('sector')
        if sector:
            queryset = queryset.filter(sector=sector)
        
        return queryset.order_by('symbol')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exchanges'] = Stock.objects.values_list('exchange', flat=True).distinct()
        context['sectors'] = Stock.objects.values_list('sector', flat=True).distinct().exclude(sector__isnull=True)
        context['query'] = self.request.GET.get('q', '')
        context['selected_exchange'] = self.request.GET.get('exchange', '')
        context['selected_sector'] = self.request.GET.get('sector', '')
        return context

class StockDetailView(DetailView):
    """Detailed view of a single stock"""
    model = Stock
    template_name = 'trading/stock_detail.html'
    context_object_name = 'stock'
    slug_field = 'symbol'
    slug_url_kwarg = 'symbol'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stock = self.get_object()
        
        # Get market status for this stock's exchange
        context['market_status'] = get_market_status_for_stock(stock)
        
        # Get recent price history
        context['price_history'] = StockPrice.objects.filter(
            stock=stock
        ).order_by('-date')[:30]
        
        # Get technical indicators
        try:
            tech_indicators = stock.technical_indicators
            context['technical_indicators'] = tech_indicators
            
            # Calculate support and resistance distances
            if stock.current_price and tech_indicators.support_level:
                tech_indicators.support_distance = stock.current_price - tech_indicators.support_level
            
            if stock.current_price and tech_indicators.resistance_level:
                tech_indicators.resistance_distance = tech_indicators.resistance_level - stock.current_price
                
        except:
            context['technical_indicators'] = None
        
        # Check if user has this stock in portfolio
        if self.request.user.is_authenticated:
            try:
                context['portfolio_item'] = Portfolio.objects.get(
                    user=self.request.user, 
                    stock=stock
                )
            except Portfolio.DoesNotExist:
                context['portfolio_item'] = None
            
            # Check if stock is in user's watchlist
            context['in_watchlist'] = Watchlist.objects.filter(
                user=self.request.user,
                stock=stock
            ).exists()
        
        return context

@login_required
def portfolio_view(request):
    """User's portfolio with detailed holdings"""
    portfolio_items = Portfolio.objects.filter(
        user=request.user
    ).select_related('stock').order_by('-current_value')
    
    # Update current values for each portfolio item
    for item in portfolio_items:
        if item.stock.current_price:
            item.current_value = item.quantity * item.stock.current_price
            item.gain_loss = item.current_value - (item.quantity * item.average_price)
            if item.average_price > 0:
                item.gain_loss_percent = (item.gain_loss / (item.quantity * item.average_price)) * 100
            item.save()
    
    # Portfolio summary
    total_value = sum(item.current_value or 0 for item in portfolio_items)
    total_invested = sum(item.quantity * item.average_price for item in portfolio_items)
    total_gain_loss = total_value - total_invested
    
    context = {
        'portfolio_items': portfolio_items,
        'total_value': total_value,
        'total_invested': total_invested,
        'total_gain_loss': total_gain_loss,
        'gain_loss_percent': (total_gain_loss / total_invested * 100) if total_invested > 0 else 0,
    }
    return render(request, 'trading/portfolio.html', context)

@login_required
def trade_stock(request, symbol):
    """Trade (buy/sell) a stock"""
    stock = get_object_or_404(Stock, symbol=symbol)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's current holding of this stock
    try:
        portfolio_item = Portfolio.objects.get(user=request.user, stock=stock)
        current_quantity = portfolio_item.quantity
    except Portfolio.DoesNotExist:
        portfolio_item = None
        current_quantity = 0
    
    if request.method == 'POST':
        trade_type = request.POST.get('trade_type')
        order_type = request.POST.get('order_type', 'market')
        quantity = int(request.POST.get('quantity', 0))
        price = Decimal(request.POST.get('price', stock.current_price or 0))
        stop_loss_price = request.POST.get('stop_loss_price')
        
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0.')
            return redirect('stock_detail', symbol=symbol)
        
        total_amount = quantity * price
        
        # Convert stop_loss_price to Decimal if provided
        if stop_loss_price:
            try:
                stop_loss_price = Decimal(stop_loss_price)
            except:
                stop_loss_price = None
        
        if trade_type == 'buy':
            # Check if user has sufficient balance
            if user_profile.account_balance < total_amount:
                messages.error(request, 'Insufficient account balance.')
                return redirect('stock_detail', symbol=symbol)
            
            # Create trade record
            trade = Trade.objects.create(
                user=request.user,
                stock=stock,
                trade_type='buy',
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_loss_price=stop_loss_price,
                total_amount=total_amount,
                status='executed',
                execution_date=timezone.now()
            )
            
            # Update user's balance
            user_profile.account_balance -= total_amount
            user_profile.save()
            
            # Update or create portfolio item
            if portfolio_item:
                # Calculate new average price
                total_shares = portfolio_item.quantity + quantity
                total_cost = (portfolio_item.quantity * portfolio_item.average_price) + total_amount
                portfolio_item.average_price = total_cost / total_shares
                portfolio_item.quantity = total_shares
                portfolio_item.save()
            else:
                Portfolio.objects.create(
                    user=request.user,
                    stock=stock,
                    quantity=quantity,
                    average_price=price
                )
            
            # Create stop-loss order if specified
            if stop_loss_price and stop_loss_price < stock.current_price:
                StopLossOrder.objects.create(
                    user=request.user,
                    stock=stock,
                    quantity=quantity,
                    stop_price=stop_loss_price,
                    status='active'
                )
                messages.success(request, f'Successfully bought {quantity} shares of {stock.symbol} with stop-loss at ${stop_loss_price}!')
            else:
                messages.success(request, f'Successfully bought {quantity} shares of {stock.symbol}!')
            
        elif trade_type == 'sell':
            # Check if user has enough shares to sell
            if current_quantity < quantity:
                messages.error(request, 'Insufficient shares to sell.')
                return redirect('stock_detail', symbol=symbol)
            
            # Create trade record
            trade = Trade.objects.create(
                user=request.user,
                stock=stock,
                trade_type='sell',
                order_type=order_type,
                quantity=quantity,
                price=price,
                total_amount=total_amount,
                status='executed',
                execution_date=timezone.now()
            )
            
            # Update user's balance
            user_profile.account_balance += total_amount
            user_profile.save()
            
            # Update portfolio item
            if portfolio_item:
                portfolio_item.quantity -= quantity
                if portfolio_item.quantity == 0:
                    portfolio_item.delete()
                else:
                    portfolio_item.save()
            
            messages.success(request, f'Successfully sold {quantity} shares of {stock.symbol}!')
        
        return redirect('stock_detail', symbol=symbol)
    
    # Get user's active stop-loss orders for this stock
    stop_loss_orders = StopLossOrder.objects.filter(
        user=request.user,
        stock=stock,
        status='active'
    ).order_by('-created_at')
    
    context = {
        'stock': stock,
        'user_profile': user_profile,
        'current_quantity': current_quantity,
        'portfolio_item': portfolio_item,
        'stop_loss_orders': stop_loss_orders,
    }
    return render(request, 'trading/trade.html', context)

@login_required
def watchlist_view(request):
    """User's watchlist"""
    watchlist_items = Watchlist.objects.filter(
        user=request.user
    ).select_related('stock').order_by('stock__symbol')
    
    context = {
        'watchlist_items': watchlist_items,
    }
    return render(request, 'trading/watchlist.html', context)

@login_required
def toggle_watchlist(request, symbol):
    """Add or remove stock from watchlist"""
    if request.method == 'POST':
        stock = get_object_or_404(Stock, symbol=symbol)
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            stock=stock
        )
        
        if created:
            messages.success(request, f'{stock.symbol} added to watchlist.')
        else:
            watchlist_item.delete()
            messages.success(request, f'{stock.symbol} removed from watchlist.')
    
    return redirect('stock_detail', symbol=symbol)

@login_required
def trade_history(request):
    """User's trading history"""
    trades = Trade.objects.filter(
        user=request.user
    ).select_related('stock').order_by('-order_date')
    
    paginator = Paginator(trades, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'trades': page_obj,
    }
    return render(request, 'trading/trade_history.html', context)

@login_required
def stop_loss_orders(request):
    """View active stop-loss orders"""
    orders = StopLossOrder.objects.filter(
        user=request.user,
        status='active'
    ).select_related('stock').order_by('-created_at')
    
    # Calculate trigger distances for each order
    for order in orders:
        if order.stock.current_price:
            order.trigger_distance = order.stock.current_price - order.stop_price
            order.trigger_distance_percent = (order.trigger_distance / order.stock.current_price) * 100
            order.near_trigger = order.stock.current_price <= order.stop_price * 1.05  # Within 5% of trigger
        else:
            order.trigger_distance = None
            order.trigger_distance_percent = None
            order.near_trigger = False
    
    context = {
        'orders': orders,
    }
    return render(request, 'trading/stop_loss_orders.html', context)

@login_required
def cancel_stop_loss(request, order_id):
    """Cancel a stop-loss order"""
    if request.method == 'POST':
        try:
            order = StopLossOrder.objects.get(id=order_id, user=request.user, status='active')
            order.status = 'cancelled'
            order.save()
            messages.success(request, f'Stop-loss order for {order.stock.symbol} has been cancelled.')
        except StopLossOrder.DoesNotExist:
            messages.error(request, 'Stop-loss order not found or already cancelled.')
    
    return redirect('stop_loss_orders')

def stock_search_api(request):
    """API endpoint for stock search autocomplete"""
    query = request.GET.get('q', '')
    if len(query) >= 2:
        stocks = Stock.objects.filter(
            Q(symbol__icontains=query) | Q(name__icontains=query)
        )[:10]
        
        results = [
            {
                'symbol': stock.symbol,
                'name': stock.name,
                'current_price': str(stock.current_price) if stock.current_price else None,
            }
            for stock in stocks
        ]
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

def get_market_status_for_stock(stock):
    """Get market status for a specific stock's exchange"""
    from .models import TradingHours, MarketHoliday
    from django.utils import timezone
    
    try:
        trading_hours = TradingHours.objects.get(exchange=stock.exchange)
        
        # Check for holidays first
        today = timezone.now().date()
        holiday = MarketHoliday.objects.filter(
            exchange=stock.exchange,
            date=today
        ).first()
        
        if holiday:
            if holiday.is_partial_day:
                return {
                    'is_open': False,
                    'status': 'partial_holiday',
                    'message': f"Early close today - {holiday.name}",
                    'early_close_time': holiday.early_close_time,
                    'trading_hours': trading_hours
                }
            else:
                return {
                    'is_open': False,
                    'status': 'holiday',
                    'message': f"Market closed - {holiday.name}",
                    'trading_hours': trading_hours
                }
        
        # Get regular market status
        market_status = trading_hours.get_market_status()
        return {
            'is_open': market_status['is_open'],
            'status': 'open' if market_status['is_open'] else 'closed',
            'message': market_status['status_message'],
            'local_time': market_status['local_time'],
            'trading_hours': trading_hours
        }
        
    except TradingHours.DoesNotExist:
        return {
            'is_open': None,
            'status': 'unknown',
            'message': f"Trading hours not available for {stock.exchange}",
            'trading_hours': None
        }

def get_all_market_status():
    """Get market status for all exchanges"""
    from .models import TradingHours
    
    market_statuses = {}
    for trading_hours in TradingHours.objects.all():
        status = trading_hours.get_market_status()
        market_statuses[trading_hours.exchange] = {
            'exchange': trading_hours.exchange,
            'timezone': trading_hours.timezone,
            'is_open': status['is_open'],
            'message': status['status_message'],
            'local_time': status['local_time'],
            'market_open': trading_hours.market_open,
            'market_close': trading_hours.market_close,
        }
    
    return market_statuses

def market_hours_view(request):
    """Display trading hours for all exchanges"""
    from .models import TradingHours, MarketHoliday
    from django.utils import timezone
    import pytz
    
    # Get all trading hours with current status
    market_statuses = []
    for trading_hours in TradingHours.objects.all():
        status = trading_hours.get_market_status()
        
        # Check for today's holidays
        today = timezone.now().date()
        holiday = MarketHoliday.objects.filter(
            exchange=trading_hours.exchange,
            date=today
        ).first()
        
        # Get upcoming holidays
        upcoming_holidays = MarketHoliday.objects.filter(
            exchange=trading_hours.exchange,
            date__gt=today
        ).order_by('date')[:3]
        
        market_statuses.append({
            'trading_hours': trading_hours,
            'is_open': status['is_open'],
            'status_message': status['status_message'],
            'local_time': status['local_time'],
            'exchange_timezone': status['exchange_timezone'],
            'today_holiday': holiday,
            'upcoming_holidays': upcoming_holidays,
        })
    
    context = {
        'market_statuses': market_statuses,
        'current_time': timezone.now(),
    }
    return render(request, 'trading/market_hours.html', context)

def philippine_trading_times(request):
    """Display trading hours for all exchanges in Philippine time"""
    from .models import TradingHours, MarketHoliday
    from django.utils import timezone
    import pytz
    
    philippine_tz = pytz.timezone('Asia/Manila')
    current_time = timezone.now().astimezone(philippine_tz)
    
    # Trading hours conversion to Philippine time
    trading_schedules = []
    
    for trading_hours in TradingHours.objects.all():
        exchange_tz = pytz.timezone(trading_hours.timezone)
        
        # Create a dummy date for time conversion (today)
        dummy_date = current_time.date()
        
        # Convert market open/close to Philippine time
        market_open_exchange = exchange_tz.localize(
            timezone.datetime.combine(dummy_date, trading_hours.market_open)
        )
        market_close_exchange = exchange_tz.localize(
            timezone.datetime.combine(dummy_date, trading_hours.market_close)
        )
        
        market_open_ph = market_open_exchange.astimezone(philippine_tz)
        market_close_ph = market_close_exchange.astimezone(philippine_tz)
        
        # Handle pre-market times if available
        premarket_open_ph = None
        if trading_hours.premarket_open:
            premarket_open_exchange = exchange_tz.localize(
                timezone.datetime.combine(dummy_date, trading_hours.premarket_open)
            )
            premarket_open_ph = premarket_open_exchange.astimezone(philippine_tz)
        
        # Handle after-hours times if available
        afterhours_close_ph = None
        if trading_hours.afterhours_close:
            afterhours_close_exchange = exchange_tz.localize(
                timezone.datetime.combine(dummy_date, trading_hours.afterhours_close)
            )
            afterhours_close_ph = afterhours_close_exchange.astimezone(philippine_tz)
        
        # Get current market status
        status = trading_hours.get_market_status()
        
        # Determine trading opportunity for Philippine traders
        ph_trading_opportunity = "Excellent"  # Default
        if market_open_ph.hour >= 22 or market_close_ph.hour <= 6:
            ph_trading_opportunity = "Challenging (Late Night/Early Morning)"
        elif market_open_ph.hour >= 9 and market_close_ph.hour <= 18:
            ph_trading_opportunity = "Excellent (Business Hours)"
        elif market_open_ph.hour >= 6 and market_close_ph.hour <= 22:
            ph_trading_opportunity = "Good (Manageable Hours)"
        
        trading_schedules.append({
            'exchange': trading_hours.exchange,
            'exchange_timezone': trading_hours.timezone,
            'market_open_ph': market_open_ph,
            'market_close_ph': market_close_ph,
            'premarket_open_ph': premarket_open_ph,
            'afterhours_close_ph': afterhours_close_ph,
            'is_open': status['is_open'],
            'status_message': status['status_message'],
            'ph_trading_opportunity': ph_trading_opportunity,
            'duration_hours': (market_close_ph - market_open_ph).total_seconds() / 3600,
        })
    
    # Sort by market open time in Philippine time
    trading_schedules.sort(key=lambda x: x['market_open_ph'].hour)
    
    context = {
        'trading_schedules': trading_schedules,
        'current_ph_time': current_time,
        'philippine_timezone': 'Asia/Manila',
    }
    return render(request, 'trading/philippine_trading_times.html', context)
