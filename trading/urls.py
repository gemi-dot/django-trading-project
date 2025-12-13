from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home and dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Learning and Education
    path('learn/', views.learning_dashboard, name='learning_dashboard'),
    path('learn/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('performance/', views.trading_performance, name='trading_performance'),
    
    # Stock-related URLs
    path('stocks/', views.StockListView.as_view(), name='stock_list'),
    path('stocks/<str:symbol>/', views.StockDetailView.as_view(), name='stock_detail'),
    path('stocks/<str:symbol>/trade/', views.trade_stock, name='trade_stock'),
    
    # Portfolio and trading
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('trades/', views.trade_history, name='trade_history'),
    
    # Stop Loss Orders
    path('stop-loss/', views.stop_loss_orders, name='stop_loss_orders'),
    path('stop-loss/cancel/<int:order_id>/', views.cancel_stop_loss, name='cancel_stop_loss'),
    
    # Watchlist
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watchlist/toggle/<str:symbol>/', views.toggle_watchlist, name='toggle_watchlist'),
    
    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/signup/', views.signup, name='signup'),
    
    # API endpoints
    path('api/stock-search/', views.stock_search_api, name='stock_search_api'),
    
    # Market hours
    path('market-hours/', views.market_hours_view, name='market_hours'),
    path('philippine-trading-times/', views.philippine_trading_times, name='philippine_trading_times'),
]