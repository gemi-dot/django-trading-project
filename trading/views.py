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
                    TradingLesson, UserLessonProgress, TradingPerformance, SkillAssessment, 
                    PracticeModule, UserPracticeSession, LearningPath, UserLearningProgress)

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
    
    # Get technical indicators data for dashboard charts
    from .models import TechnicalIndicators
    import json
    
    # Get technical indicators for portfolio stocks or popular stocks
    tech_data = {
        'labels': [],
        'rsi_data': [],
        'macd_data': [],
        'macd_signal': [],
        'prices': [],
        'sma_20': [],
        'sma_50': [],
        'upper_band': [],
        'lower_band': [],
        # Additional data for advanced indicators
        'overall_signals': [],
        'signal_strengths': [],
        'volume_ratios': [],
        'trend_strengths': [],
        'bb_widths': []
    }
    
    # Get stocks for indicators (portfolio stocks first, then popular stocks)
    stocks_for_indicators = []
    if portfolio_items.exists():
        stocks_for_indicators = [item.stock for item in portfolio_items[:5]]
    else:
        # Get top 5 stocks with current prices if user has no portfolio
        stocks_for_indicators = Stock.objects.filter(
            current_price__isnull=False
        ).order_by('-current_price')[:5]
    
    for stock in stocks_for_indicators:
        try:
            indicators = TechnicalIndicators.objects.get(stock=stock)
            tech_data['labels'].append(stock.symbol)
            tech_data['rsi_data'].append(float(indicators.rsi_14) if indicators.rsi_14 else 50)
            tech_data['macd_data'].append(float(indicators.macd_line) if indicators.macd_line else 0)
            tech_data['macd_signal'].append(float(indicators.macd_signal) if indicators.macd_signal else 0)
            tech_data['prices'].append(float(stock.current_price) if stock.current_price else 100)
            tech_data['sma_20'].append(float(indicators.sma_20) if indicators.sma_20 else 0)
            tech_data['sma_50'].append(float(indicators.sma_50) if indicators.sma_50 else 0)
            tech_data['upper_band'].append(float(indicators.bb_upper) if indicators.bb_upper else 0)
            tech_data['lower_band'].append(float(indicators.bb_lower) if indicators.bb_lower else 0)
            
            # Advanced indicators data
            tech_data['overall_signals'].append(indicators.overall_signal or 'hold')
            tech_data['signal_strengths'].append(float(indicators.signal_strength) if indicators.signal_strength else 50)
            tech_data['volume_ratios'].append(float(indicators.volume_ratio) if indicators.volume_ratio else 1.0)
            tech_data['trend_strengths'].append(float(indicators.trend_strength) if indicators.trend_strength else 50)
            tech_data['bb_widths'].append(float(indicators.bb_width) if indicators.bb_width else 0)
            
        except TechnicalIndicators.DoesNotExist:
            # Use calculated sample data if no technical indicators found
            price = float(stock.current_price) if stock.current_price else 100
            tech_data['labels'].append(stock.symbol)
            tech_data['rsi_data'].append(50)  # Neutral RSI
            tech_data['macd_data'].append(0)
            tech_data['macd_signal'].append(0)
            tech_data['prices'].append(price)
            tech_data['sma_20'].append(price * 0.98)
            tech_data['sma_50'].append(price * 0.95)
            tech_data['upper_band'].append(price * 1.05)
            tech_data['lower_band'].append(price * 0.95)
            
            # Sample advanced indicators
            tech_data['overall_signals'].append('hold')
            tech_data['signal_strengths'].append(50)
            tech_data['volume_ratios'].append(1.0)
            tech_data['trend_strengths'].append(50)
            tech_data['bb_widths'].append(price * 0.1)
    
    context = {
        'user_profile': user_profile,
        'portfolio_items': portfolio_items,
        'total_portfolio_value': total_portfolio_value,
        'total_invested': total_invested,
        'total_gain_loss': total_gain_loss,
        'gain_loss_percent': gain_loss_percent,
        'recent_trades': recent_trades,
        'watchlist_items': watchlist_items,
        'tech_data_json': json.dumps(tech_data),
    }
    return render(request, 'trading/dashboard.html', context)

@login_required
def skill_assessment_dashboard(request):
    """Comprehensive skill assessment and development dashboard"""
    from .models import SkillAssessment, PracticeModule, UserPracticeSession, LearningPath, UserLearningProgress
    
    # Get or create skill assessments for all categories
    skill_categories = [
        'technical_analysis', 'fundamental_analysis', 'risk_management', 
        'market_psychology', 'position_sizing', 'entry_timing', 
        'exit_strategy', 'portfolio_management'
    ]
    
    assessments = {}
    for category in skill_categories:
        assessment, created = SkillAssessment.objects.get_or_create(
            user=request.user,
            category=category,
            defaults={
                'current_level': 1,
                'target_level': 4,
                'knowledge_score': 30,
                'practical_score': 20,
                'consistency_score': 15,
            }
        )
        assessment.calculate_overall_score()
        assessments[category] = assessment
    
    # Calculate overall trading proficiency
    total_score = sum(a.overall_score for a in assessments.values())
    overall_proficiency = total_score / len(assessments)
    
    # Get recommended practice modules
    user_level = int(overall_proficiency // 10) + 1
    recommended_modules = PracticeModule.objects.filter(
        required_level__lte=user_level,
        is_active=True
    ).order_by('difficulty', 'title')[:6]
    
    # Recent practice sessions
    recent_sessions = UserPracticeSession.objects.filter(
        user=request.user
    ).select_related('module').order_by('-started_at')[:10]
    
    # Learning path progress
    learning_progress = UserLearningProgress.objects.filter(
        user=request.user,
        is_completed=False
    ).select_related('path').first()
    
    # Generate personalized recommendations
    recommendations = generate_skill_recommendations(request.user, assessments)
    
    context = {
        'assessments': assessments,
        'overall_proficiency': overall_proficiency,
        'overall_grade': get_grade_from_score(overall_proficiency),
        'recommended_modules': recommended_modules,
        'recent_sessions': recent_sessions,
        'learning_progress': learning_progress,
        'recommendations': recommendations,
        'skill_categories': skill_categories,
    }
    return render(request, 'trading/skill_assessment_dashboard.html', context)

def generate_skill_recommendations(user, assessments):
    """Generate personalized skill development recommendations"""
    recommendations = []
    
    # Find weakest skills
    weakest_skills = sorted(assessments.items(), key=lambda x: x[1].overall_score)[:3]
    
    for skill_name, assessment in weakest_skills:
        recs = assessment.recommend_next_steps()
        for rec in recs:
            rec['skill'] = skill_name.replace('_', ' ').title()
            recommendations.append(rec)
    
    # Add trading performance based recommendations
    try:
        performance = user.trading_performance
        
        if performance.win_rate < 50:
            recommendations.append({
                'type': 'strategy',
                'priority': 'high',
                'skill': 'Overall Strategy',
                'action': 'Focus on high-probability setups only',
                'time_estimate': 'Daily review'
            })
        
        if performance.stop_loss_usage_rate < 70:
            recommendations.append({
                'type': 'risk',
                'priority': 'critical',
                'skill': 'Risk Management',
                'action': 'Practice with stop-loss on every trade',
                'time_estimate': 'Immediate implementation'
            })
            
    except:
        pass
    
    return recommendations[:6]  # Return top 6 recommendations

def get_grade_from_score(score):
    """Convert numeric score to letter grade"""
    if score >= 95: return 'A+'
    elif score >= 90: return 'A'
    elif score >= 85: return 'A-'
    elif score >= 80: return 'B+'
    elif score >= 75: return 'B'
    elif score >= 70: return 'B-'
    elif score >= 65: return 'C+'
    elif score >= 60: return 'C'
    elif score >= 55: return 'C-'
    else: return 'F'

@login_required
def practice_module_detail(request, module_id):
    """Practice module interface"""
    from .models import PracticeModule, UserPracticeSession
    
    module = get_object_or_404(PracticeModule, id=module_id, is_active=True)
    
    # Check if user has required skill level
    user_sessions = UserPracticeSession.objects.filter(
        user=request.user,
        module=module
    ).order_by('-started_at')
    
    attempts_used = user_sessions.count()
    can_attempt = attempts_used < module.max_attempts
    
    # Get user's best score
    best_session = user_sessions.filter(status='completed').order_by('-score').first()
    best_score = best_session.score if best_session else 0
    
    if request.method == 'POST' and can_attempt:
        # Start new practice session
        session = UserPracticeSession.objects.create(
            user=request.user,
            module=module,
            attempt_number=attempts_used + 1
        )
        
        # Redirect to practice interface based on module type
        if module.module_type == 'quiz':
            return redirect('practice_quiz', session_id=session.id)
        elif module.module_type == 'simulation':
            return redirect('practice_simulation', session_id=session.id)
        elif module.module_type == 'pattern_recognition':
            return redirect('practice_pattern_recognition', session_id=session.id)
    
    context = {
        'module': module,
        'user_sessions': user_sessions,
        'attempts_used': attempts_used,
        'can_attempt': can_attempt,
        'best_score': best_score,
    }
    return render(request, 'trading/practice_module_detail.html', context)

@login_required
def practice_quiz(request, session_id):
    """Interactive quiz practice"""
    from .models import UserPracticeSession
    
    session = get_object_or_404(UserPracticeSession, id=session_id, user=request.user)
    
    if session.status == 'completed':
        return redirect('practice_results', session_id=session.id)
    
    # Mark session as in progress
    if session.status == 'started':
        session.status = 'in_progress'
        session.save()
    
    # Get quiz questions from module content
    questions = session.module.content_data.get('questions', [])
    
    if request.method == 'POST':
        # Process quiz submission
        user_answers = {}
        score = 0
        total_questions = len(questions)
        
        for i, question in enumerate(questions):
            answer_key = f'question_{i}'
            user_answer = request.POST.get(answer_key)
            user_answers[i] = user_answer
            
            if user_answer == question.get('correct_answer'):
                score += 1
        
        # Calculate final score
        final_score = (score / total_questions) * 100 if total_questions > 0 else 0
        
        # Update session
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.score = final_score
        session.accuracy = final_score  # For quiz, accuracy = score
        session.answers = user_answers
        
        # Analyze performance
        strengths = []
        weaknesses = []
        
        for i, question in enumerate(questions):
            if user_answers.get(i) == question.get('correct_answer'):
                strengths.append(question.get('topic', 'General'))
            else:
                weaknesses.append(question.get('topic', 'General'))
        
        session.strengths_identified = list(set(strengths))
        session.weaknesses_identified = list(set(weaknesses))
        
        if final_score < 70:
            session.recommended_focus = "Review fundamental concepts and retake practice modules"
        elif final_score < 85:
            session.recommended_focus = "Focus on areas where you missed questions"
        else:
            session.recommended_focus = "Excellent work! Try more advanced modules"
        
        session.save()
        
        return redirect('practice_results', session_id=session.id)
    
    context = {
        'session': session,
        'questions': questions,
    }
    return render(request, 'trading/practice_quiz.html', context)

@login_required
def practice_results(request, session_id):
    """Display practice session results and recommendations"""
    from .models import UserPracticeSession, SkillAssessment
    
    session = get_object_or_404(UserPracticeSession, id=session_id, user=request.user)
    
    # Update skill assessments based on performance
    if session.status == 'completed' and session.score >= session.module.passing_score:
        # Apply skill improvements
        improvements = session.calculate_skill_improvement()
        
        if improvements.get('points', 0) > 0:
            # Update related skill assessments
            for skill_assessment in session.module.target_skills.filter(user=request.user):
                skill_assessment.practical_score += improvements['points']
                skill_assessment.practical_score = min(skill_assessment.practical_score, 100)
                skill_assessment.calculate_overall_score()
    
    # Get recommendations for next steps
    next_recommendations = []
    
    if session.score >= 85:
        # Suggest advanced modules
        advanced_modules = PracticeModule.objects.filter(
            difficulty__in=['advanced', 'expert'],
            is_active=True
        ).exclude(id=session.module.id)[:3]
        
        for module in advanced_modules:
            next_recommendations.append({
                'type': 'advance',
                'title': f"Try {module.title}",
                'url': f"/practice/module/{module.id}/",
                'difficulty': module.difficulty
            })
    
    elif session.score < 70:
        # Suggest reviewing basics
        basic_modules = PracticeModule.objects.filter(
            difficulty='beginner',
            is_active=True
        ).exclude(id=session.module.id)[:3]
        
        for module in basic_modules:
            next_recommendations.append({
                'type': 'review',
                'title': f"Review with {module.title}",
                'url': f"/practice/module/{module.id}/",
                'difficulty': module.difficulty
            })
    
    context = {
        'session': session,
        'next_recommendations': next_recommendations,
        'grade': get_grade_from_score(session.score),
    }
    return render(request, 'trading/practice_results.html', context)

@login_required
def stock_list(request):
    """Stock list view with search and filtering"""
    search_query = request.GET.get('search', '')
    
    # Start with all stocks
    stocks = Stock.objects.all()
    
    # Apply search filter
    if search_query:
        stocks = stocks.filter(
            Q(symbol__icontains=search_query) | 
            Q(name__icontains=search_query)
        )
    
    # Order by symbol
    stocks = stocks.order_by('symbol')
    
    # Pagination
    paginator = Paginator(stocks, 20)  # Show 20 stocks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'stocks': page_obj,
        'search_query': search_query,
        'total_stocks': stocks.count(),
    }
    return render(request, 'trading/stock_list.html', context)

@login_required
def stock_detail(request, symbol):
    """Stock detail view with technical indicators and trading interface"""
    stock = get_object_or_404(Stock, symbol=symbol.upper())
    
    # Get technical indicators if available
    try:
        technical_indicators = stock.technical_indicators
    except:
        technical_indicators = None
    
    # Check if stock is in user's watchlist
    in_watchlist = Watchlist.objects.filter(user=request.user, stock=stock).exists()
    
    # Get user's portfolio position for this stock
    try:
        portfolio_position = Portfolio.objects.get(user=request.user, stock=stock)
    except Portfolio.DoesNotExist:
        portfolio_position = None
    
    # Get recent trades for this stock by the user
    recent_trades = Trade.objects.filter(
        user=request.user, 
        stock=stock
    ).order_by('-order_date')[:5]
    
    # Get recent price history (last 30 days)
    recent_prices = StockPrice.objects.filter(
        stock=stock
    ).order_by('-date')[:30]
    
    context = {
        'stock': stock,
        'technical_indicators': technical_indicators,
        'in_watchlist': in_watchlist,
        'portfolio_position': portfolio_position,
        'recent_trades': recent_trades,
        'recent_prices': recent_prices,
    }
    return render(request, 'trading/stock_detail.html', context)

@login_required
def market_hours(request):
    """Market hours and trading sessions view"""
    from .models import TradingHours, MarketHoliday
    import pytz
    from datetime import datetime
    
    # Get all trading hours for different exchanges
    trading_hours = TradingHours.objects.all().order_by('exchange')
    
    # Get current market status for each exchange
    market_status = {}
    current_time = timezone.now()
    
    for hours in trading_hours:
        status_info = hours.get_market_status(current_time)
        market_status[hours.exchange] = status_info
    
    # Get upcoming market holidays
    upcoming_holidays = MarketHoliday.objects.filter(
        date__gte=current_time.date()
    ).order_by('date')[:10]
    
    # Calculate trading session times for different timezones
    timezones_info = []
    timezone_list = [
        ('America/New_York', 'New York (EST/EDT)'),
        ('Europe/London', 'London (GMT/BST)'),
        ('Asia/Tokyo', 'Tokyo (JST)'),
        ('Asia/Hong_Kong', 'Hong Kong (HKT)'),
        ('Asia/Manila', 'Manila (PHT)'),
        ('Asia/Singapore', 'Singapore (SGT)'),
    ]
    
    for tz_name, tz_display in timezone_list:
        try:
            tz = pytz.timezone(tz_name)
            local_time = current_time.astimezone(tz)
            timezones_info.append({
                'name': tz_display,
                'time': local_time,
                'timezone': tz_name,
            })
        except:
            pass
    
    context = {
        'trading_hours': trading_hours,
        'market_status': market_status,
        'upcoming_holidays': upcoming_holidays,
        'timezones_info': timezones_info,
        'current_time': current_time,
    }
    return render(request, 'trading/market_hours.html', context)

@login_required
def philippine_trading_times(request):
    """Philippine stock market trading times and schedule"""
    from .models import TradingHours, MarketHoliday
    import pytz
    from datetime import datetime, time
    
    # Get Philippine timezone
    ph_tz = pytz.timezone('Asia/Manila')
    current_time = timezone.now()
    ph_current_time = current_time.astimezone(ph_tz)
    
    # Philippine Stock Exchange (PSE) trading hours
    pse_trading_schedule = {
        'pre_open': {
            'start': time(9, 0),   # 9:00 AM
            'end': time(9, 30),    # 9:30 AM
            'description': 'Pre-opening session for order entry'
        },
        'morning_session': {
            'start': time(9, 30),  # 9:30 AM
            'end': time(12, 0),    # 12:00 PM
            'description': 'Morning trading session'
        },
        'lunch_break': {
            'start': time(12, 0),  # 12:00 PM
            'end': time(13, 30),   # 1:30 PM
            'description': 'Lunch break - market closed'
        },
        'afternoon_session': {
            'start': time(13, 30), # 1:30 PM
            'end': time(15, 30),   # 3:30 PM
            'description': 'Afternoon trading session'
        },
        'runoff': {
            'start': time(15, 30), # 3:30 PM
            'end': time(15, 40),   # 3:40 PM
            'description': 'Runoff period for closing trades'
        }
    }
    
    # Determine current market status
    current_time_only = ph_current_time.time()
    current_status = 'closed'
    next_session = None
    time_to_next = None
    
    if time(9, 0) <= current_time_only < time(9, 30):
        current_status = 'pre_open'
        next_session = 'Morning Trading'
        time_to_next = datetime.combine(ph_current_time.date(), time(9, 30)) - datetime.combine(ph_current_time.date(), current_time_only)
    elif time(9, 30) <= current_time_only < time(12, 0):
        current_status = 'morning_session'
        next_session = 'Lunch Break'
        time_to_next = datetime.combine(ph_current_time.date(), time(12, 0)) - datetime.combine(ph_current_time.date(), current_time_only)
    elif time(12, 0) <= current_time_only < time(13, 30):
        current_status = 'lunch_break'
        next_session = 'Afternoon Trading'
        time_to_next = datetime.combine(ph_current_time.date(), time(13, 30)) - datetime.combine(ph_current_time.date(), current_time_only)
    elif time(13, 30) <= current_time_only < time(15, 30):
        current_status = 'afternoon_session'
        next_session = 'Runoff Period'
        time_to_next = datetime.combine(ph_current_time.date(), time(15, 30)) - datetime.combine(ph_current_time.date(), current_time_only)
    elif time(15, 30) <= current_time_only < time(15, 40):
        current_status = 'runoff'
        next_session = 'Market Closed'
        time_to_next = datetime.combine(ph_current_time.date(), time(15, 40)) - datetime.combine(ph_current_time.date(), current_time_only)
    
    # Get Philippine market holidays
    ph_holidays = MarketHoliday.objects.filter(
        exchange='PSE',
        date__gte=ph_current_time.date()
    ).order_by('date')[:10]
    
    # Check if today is a holiday or weekend
    is_weekend = ph_current_time.weekday() >= 5  # Saturday = 5, Sunday = 6
    is_holiday = MarketHoliday.objects.filter(
        exchange='PSE',
        date=ph_current_time.date()
    ).exists()
    
    if is_weekend or is_holiday:
        current_status = 'closed_holiday'
        if is_weekend:
            next_session = 'Opens Monday 9:00 AM'
        else:
            next_session = 'Holiday - Check schedule'
    
    # PSE sector information
    pse_sectors = [
        {'name': 'Banking', 'code': 'BNK', 'description': 'Commercial banks and financial services'},
        {'name': 'Mining & Oil', 'code': 'MIN', 'description': 'Mining companies and oil exploration'},
        {'name': 'Property', 'code': 'PRO', 'description': 'Real estate and property development'},
        {'name': 'Industrial', 'code': 'IND', 'description': 'Manufacturing and industrial companies'},
        {'name': 'Services', 'code': 'SVC', 'description': 'Service sector companies'},
        {'name': 'Holding Firms', 'code': 'HLD', 'description': 'Investment and holding companies'},
    ]
    
    # Trading fees and costs
    trading_costs = {
        'broker_commission': '0.25%',
        'sales_tax': '0.60%',
        'pse_transaction_fee': '0.005%',
        'sccp_fee': '0.01%',
        'minimum_commission': 'PHP 20.00'
    }
    
    context = {
        'pse_trading_schedule': pse_trading_schedule,
        'current_status': current_status,
        'next_session': next_session,
        'time_to_next': time_to_next,
        'ph_current_time': ph_current_time,
        'ph_holidays': ph_holidays,
        'is_weekend': is_weekend,
        'is_holiday': is_holiday,
        'pse_sectors': pse_sectors,
        'trading_costs': trading_costs,
    }
    return render(request, 'trading/philippine_trading_times.html', context)

@login_required
def portfolio(request):
    """Portfolio view showing all user's holdings"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's portfolio items - include error handling for corrupted data
    try:
        portfolio_items_queryset = Portfolio.objects.filter(
            user=request.user
        ).select_related('stock')
        
        # Filter out problematic entries
        valid_portfolio_items = []
        problematic_items = []
        
        for item in portfolio_items_queryset:
            try:
                # Test if we can access stock data
                if (item.stock and 
                    item.stock.symbol and 
                    item.stock.symbol.strip() != '' and
                    item.stock.name and 
                    item.stock.name.strip() != ''):
                    valid_portfolio_items.append(item)
                else:
                    problematic_items.append(item)
            except Exception as e:
                problematic_items.append(item)
        
        # Log problematic items for debugging
        if problematic_items:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Found {len(problematic_items)} problematic portfolio entries for user {request.user.username}")
            for item in problematic_items:
                try:
                    logger.warning(f"Problematic portfolio item ID: {item.id}, Stock ID: {item.stock_id if hasattr(item, 'stock_id') else 'N/A'}")
                except:
                    logger.warning(f"Severely corrupted portfolio item ID: {item.id}")
        
        portfolio_items = valid_portfolio_items
        
    except Exception as e:
        # Fallback in case of severe database issues
        portfolio_items = []
        messages.error(request, "There was an issue loading your portfolio. Please contact support if this persists.")
    
    # Calculate detailed portfolio statistics
    portfolio_stats = {
        'total_value': Decimal('0.00'),
        'total_invested': Decimal('0.00'),
        'total_gain_loss': Decimal('0.00'),
        'gain_loss_percent': 0,
        'best_performer': None,
        'worst_performer': None,
        'total_positions': len(portfolio_items)
    }
    
    # Calculate stats for each position
    portfolio_data = []
    for item in portfolio_items:
        try:
            current_value = item.quantity * item.stock.current_price if item.stock.current_price else Decimal('0.00')
            invested_amount = item.quantity * item.average_price
            gain_loss = current_value - invested_amount
            gain_loss_percent = (gain_loss / invested_amount * 100) if invested_amount > 0 else 0
            
            portfolio_data.append({
                'item': item,
                'current_value': current_value,
                'invested_amount': invested_amount,
                'gain_loss': gain_loss,
                'gain_loss_percent': gain_loss_percent,
            })
            
            # Update totals
            portfolio_stats['total_value'] += current_value
            portfolio_stats['total_invested'] += invested_amount
            
            # Track best/worst performers
            if not portfolio_stats['best_performer'] or gain_loss_percent > portfolio_stats['best_performer']['gain_loss_percent']:
                portfolio_stats['best_performer'] = {
                    'stock': item.stock,
                    'gain_loss_percent': gain_loss_percent,
                    'gain_loss': gain_loss
                }
            
            if not portfolio_stats['worst_performer'] or gain_loss_percent < portfolio_stats['worst_performer']['gain_loss_percent']:
                portfolio_stats['worst_performer'] = {
                    'stock': item.stock,
                    'gain_loss_percent': gain_loss_percent,
                    'gain_loss': gain_loss
                }
        except Exception as e:
            # Skip problematic items in calculations
            continue
    
    # Calculate overall portfolio performance
    portfolio_stats['total_gain_loss'] = portfolio_stats['total_value'] - portfolio_stats['total_invested']
    if portfolio_stats['total_invested'] > 0:
        portfolio_stats['gain_loss_percent'] = (portfolio_stats['total_gain_loss'] / portfolio_stats['total_invested']) * 100
    
    # Add cleanup message if there were problematic items
    if 'problematic_items' in locals() and problematic_items:
        messages.warning(request, f"Some portfolio entries had data issues and were excluded from display. Contact support to clean up your portfolio data.")
    
    context = {
        'portfolio_items': portfolio_data,
        'portfolio_stats': portfolio_stats,
        'total_value': portfolio_stats['total_value'],
        'total_invested': portfolio_stats['total_invested'],
        'total_gain_loss': portfolio_stats['total_gain_loss'],
        'gain_loss_percent': portfolio_stats['gain_loss_percent'],
    }
    return render(request, 'trading/portfolio.html', context)

@login_required
def watchlist(request):
    """Watchlist view showing all user's watched stocks"""
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('stock')
    
    context = {
        'watchlist_items': watchlist_items,
    }
    return render(request, 'trading/watchlist.html', context)

@login_required
def toggle_watchlist(request, symbol):
    """Add or remove stock from watchlist"""
    if request.method == 'POST':
        stock = get_object_or_404(Stock, symbol=symbol.upper())
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            stock=stock
        )
        
        if created:
            messages.success(request, f'{stock.symbol} added to your watchlist!')
        else:
            watchlist_item.delete()
            messages.success(request, f'{stock.symbol} removed from your watchlist!')
    
    return redirect(request.META.get('HTTP_REFERER', 'watchlist'))

@login_required
def trade_history(request):
    """Trade history view"""
    trades = Trade.objects.filter(user=request.user).select_related('stock').order_by('-order_date')
    
    # Pagination
    paginator = Paginator(trades, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'trades': page_obj,
    }
    return render(request, 'trading/trade_history.html', context)

@login_required
def trade_stock(request, symbol):
    """Trade stock view - buy/sell interface"""
    stock = get_object_or_404(Stock, symbol=symbol.upper())
    
    # Get user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's current position
    try:
        portfolio_position = Portfolio.objects.get(user=request.user, stock=stock)
        current_quantity = portfolio_position.quantity
    except Portfolio.DoesNotExist:
        portfolio_position = None
        current_quantity = 0
    
    # Get active stop loss orders for this stock
    stop_loss_orders = StopLossOrder.objects.filter(
        user=request.user, 
        stock=stock, 
        status='active'
    )
    
    if request.method == 'POST':
        # Process trade order
        trade_type = request.POST.get('trade_type')
        quantity = int(request.POST.get('quantity', 0))
        price = Decimal(request.POST.get('price', '0'))
        
        if quantity > 0 and price > 0:
            # Create trade record
            trade = Trade.objects.create(
                user=request.user,
                stock=stock,
                trade_type=trade_type,
                quantity=quantity,
                price=price,
                total_amount=quantity * price,
                order_type='market'
            )
            
            # Update portfolio
            if trade_type == 'buy':
                if portfolio_position:
                    # Update existing position
                    total_quantity = portfolio_position.quantity + quantity
                    total_value = (portfolio_position.quantity * portfolio_position.average_price) + (quantity * price)
                    portfolio_position.average_price = total_value / total_quantity
                    portfolio_position.quantity = total_quantity
                    portfolio_position.save()
                else:
                    # Create new position
                    Portfolio.objects.create(
                        user=request.user,
                        stock=stock,
                        quantity=quantity,
                        average_price=price
                    )
            else:  # sell
                if portfolio_position and portfolio_position.quantity >= quantity:
                    portfolio_position.quantity -= quantity
                    if portfolio_position.quantity == 0:
                        portfolio_position.delete()
                    else:
                        portfolio_position.save()
                else:
                    messages.error(request, 'Insufficient shares to sell!')
                    return redirect('trade_stock', symbol=symbol)
            
            messages.success(request, f'Trade executed successfully: {trade_type.upper()} {quantity} shares of {stock.symbol}')
            return redirect('portfolio')
    
    context = {
        'stock': stock,
        'portfolio_position': portfolio_position,
        'portfolio_item': portfolio_position,  # For template compatibility
        'user_profile': user_profile,
        'current_quantity': current_quantity,
        'stop_loss_orders': stop_loss_orders,
    }
    return render(request, 'trading/trade.html', context)

@login_required
def stop_loss_orders(request):
    """Stop loss orders view"""
    orders = StopLossOrder.objects.filter(user=request.user).select_related('stock').order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'trading/stop_loss_orders.html', context)

@login_required
def cancel_stop_loss(request, order_id):
    """Cancel a stop loss order"""
    if request.method == 'POST':
        order = get_object_or_404(StopLossOrder, id=order_id, user=request.user)
        order.is_active = False
        order.save()
        messages.success(request, 'Stop loss order cancelled successfully!')
    
    return redirect('stop_loss_orders')

@login_required
def premarket_orders(request):
    """Pre-market orders view"""
    from .models import PreMarketStopLoss
    
    orders = PreMarketStopLoss.objects.filter(user=request.user).select_related('stock').order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'trading/premarket_orders.html', context)

@login_required
def premarket_watchlist(request):
    """Pre-market watchlist"""
    from .models import PreMarketWatchlist
    
    try:
        premarket_items = PreMarketWatchlist.objects.filter(user=request.user).select_related('stock')
    except:
        # Fallback to regular watchlist if PreMarketWatchlist doesn't exist
        premarket_items = Watchlist.objects.filter(user=request.user).select_related('stock')
    
    context = {
        'premarket_items': premarket_items,
    }
    return render(request, 'trading/premarket_watchlist.html', context)

@login_required
def premarket_stop_loss_setup(request, symbol):
    """Pre-market stop loss setup"""
    from .models import PreMarketStopLoss
    
    stock = get_object_or_404(Stock, symbol=symbol.upper())
    
    if request.method == 'POST':
        stop_price = Decimal(request.POST.get('stop_price', '0'))
        quantity = int(request.POST.get('quantity', 0))
        
        if stop_price > 0 and quantity > 0:
            PreMarketStopLoss.objects.create(
                user=request.user,
                stock=stock,
                stop_price=stop_price,
                quantity=quantity,
                status='pending'
            )
            messages.success(request, f'Pre-market stop loss order created for {stock.symbol}')
            return redirect('premarket_orders')
    
    context = {
        'stock': stock,
    }
    return render(request, 'trading/premarket_stop_loss_setup.html', context)

@login_required
def cancel_premarket_order(request, order_id):
    """Cancel a premarket order"""
    from .models import PreMarketStopLoss
    
    if request.method == 'POST':
        order = get_object_or_404(PreMarketStopLoss, id=order_id, user=request.user)
        success = order.cancel_order("User cancelled")
        
        if success:
            messages.success(request, 'Premarket order cancelled successfully!')
        else:
            messages.error(request, 'Could not cancel order. It may have already been executed.')
    
    return redirect('premarket_orders')

@login_required
def trading_performance(request):
    """Trading performance analytics"""
    try:
        performance = TradingPerformance.objects.get(user=request.user)
    except TradingPerformance.DoesNotExist:
        # Create performance record if it doesn't exist
        performance = TradingPerformance.objects.create(user=request.user)
    
    # Get recent trades for analysis
    recent_trades = Trade.objects.filter(user=request.user).order_by('-order_date')[:20]
    
    context = {
        'performance': performance,
        'recent_trades': recent_trades,
    }
    return render(request, 'trading/trading_performance.html', context)

@login_required
def learning_dashboard(request):
    """Learning dashboard with lessons and progress"""
    try:
        lessons = TradingLesson.objects.filter(is_active=True).order_by('order')
        user_progress = UserLessonProgress.objects.filter(user=request.user)
        progress_dict = {p.lesson_id: p for p in user_progress}
        
        lessons_with_progress = []
        for lesson in lessons:
            progress = progress_dict.get(lesson.id)
            lessons_with_progress.append({
                'lesson': lesson,
                'progress': progress,
                'is_completed': progress.is_completed if progress else False,
                'completion_percentage': progress.completion_percentage if progress else 0
            })
        
        context = {
            'lessons_with_progress': lessons_with_progress,
        }
    except:
        context = {'lessons_with_progress': []}
    
    return render(request, 'trading/learning_dashboard.html', context)

@login_required
def lesson_detail(request, lesson_id):
    """Individual lesson detail view"""
    try:
        lesson = get_object_or_404(TradingLesson, id=lesson_id, is_active=True)
        
        # Get or create user progress
        progress, created = UserLessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        # Mark lesson as viewed if not completed
        if not progress.is_completed:
            progress.completion_percentage = max(progress.completion_percentage, 25)
            progress.save()
        
        # Get previous and next lessons
        prev_lesson = TradingLesson.objects.filter(
            order__lt=lesson.order, 
            is_active=True
        ).order_by('-order').first()
        
        next_lesson = TradingLesson.objects.filter(
            order__gt=lesson.order, 
            is_active=True
        ).order_by('order').first()
        
        context = {
            'lesson': lesson,
            'progress': progress,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
        }
    except:
        messages.error(request, 'Lesson not found.')
        return redirect('learning_dashboard')
    
    return render(request, 'trading/lesson_detail.html', context)

# ...existing code...
