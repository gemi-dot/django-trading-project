from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home and dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Stock-related URLs
    path('stocks/', views.stock_list, name='stock_list'),
    path('stocks/<str:symbol>/', views.stock_detail, name='stock_detail'),
    path('stocks/<str:symbol>/trade/', views.trade_stock, name='trade_stock'),
    
    # Portfolio and trading
    path('portfolio/', views.portfolio, name='portfolio'),
    path('trades/', views.trade_history, name='trade_history'),
    
    # Watchlist
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/toggle/<str:symbol>/', views.toggle_watchlist, name='toggle_watchlist'),
    
    # Stop Loss Orders
    path('stop-loss/', views.stop_loss_orders, name='stop_loss_orders'),
    path('stop-loss/cancel/<int:order_id>/', views.cancel_stop_loss, name='cancel_stop_loss'),
    
    # Pre-market functionality
    path('premarket/orders/', views.premarket_orders, name='premarket_orders'),
    path('premarket/watchlist/', views.premarket_watchlist, name='premarket_watchlist'),
    path('premarket/stop-loss/<str:symbol>/', views.premarket_stop_loss_setup, name='premarket_stop_loss_setup'),
    path('premarket/cancel/<int:order_id>/', views.cancel_premarket_order, name='cancel_premarket_order'),
    
    # Market information
    path('market-hours/', views.market_hours, name='market_hours'),
    path('philippine-trading-times/', views.philippine_trading_times, name='philippine_trading_times'),
    
    # Learning and performance
    path('learning/', views.learning_dashboard, name='learning_dashboard'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('performance/', views.trading_performance, name='trading_performance'),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/signup/', views.signup, name='signup'),
    
    # Skill Assessment and Practice URLs
    path('skills/', views.skill_assessment_dashboard, name='skill_assessment_dashboard'),
    path('practice/module/<int:module_id>/', views.practice_module_detail, name='practice_module_detail'),
    path('practice/quiz/<int:session_id>/', views.practice_quiz, name='practice_quiz'),
    path('practice/results/<int:session_id>/', views.practice_results, name='practice_results'),
]