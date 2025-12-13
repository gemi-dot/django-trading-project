# Django Trading Project

A comprehensive web-based trading simulation platform built with Django. This project provides users with a virtual trading environment to learn and practice stock trading without financial risk.

## Features

### 🚀 Core Trading Features
- **Virtual Portfolio Management** - Track investments without real money
- **Stock Trading Simulation** - Buy and sell stocks with real-time data simulation
- **Watchlist Management** - Monitor favorite stocks
- **Trade History** - Complete transaction records
- **Stop-Loss Orders** - Risk management tools

### 📚 Learning Platform
- **Interactive Lessons** - Step-by-step trading education
- **Performance Analytics** - Track learning progress and trading performance
- **Market Education** - Learn trading concepts and strategies

### 🌍 Market Information
- **Global Market Hours** - Trading schedules worldwide
- **Philippine Trading Times** - Localized trading hours
- **Technical Indicators** - Basic technical analysis tools

### 👤 User Management
- **User Authentication** - Secure login and registration
- **Personal Dashboard** - Customized trading overview
- **Progress Tracking** - Monitor learning achievements

## Technology Stack

- **Backend**: Django 6.0
- **Database**: SQLite (development)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Django's built-in authentication system
- **Time Zones**: Python pytz library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/django-trading-project.git
cd django-trading-project
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install django requests pytz
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create sample data (optional):
```bash
python manage.py populate_stocks
python manage.py setup_trading_lessons
python manage.py setup_trading_hours
```

6. Start the development server:
```bash
python manage.py runserver
```

7. Visit `http://localhost:8000` to access the application

## Project Structure

```
trading_project/
├── manage.py
├── db.sqlite3
├── trading_project/          # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── trading/                  # Main trading app
    ├── models.py            # Database models
    ├── views.py             # View logic
    ├── urls.py              # URL patterns
    ├── admin.py             # Admin interface
    ├── templates/           # HTML templates
    ├── management/          # Custom management commands
    └── migrations/          # Database migrations
```

## Usage

1. **Register/Login**: Create an account or login to access features
2. **Explore Lessons**: Start with the learning dashboard to understand trading basics
3. **Browse Stocks**: View available stocks and their details
4. **Build Watchlist**: Add interesting stocks to your watchlist
5. **Start Trading**: Practice buying and selling with virtual money
6. **Track Performance**: Monitor your trading progress and analytics

## Development

This project is built for educational purposes and uses simulated data. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for educational purposes. Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.