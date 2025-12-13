from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from trading.models import TradingLesson

class Command(BaseCommand):
    help = 'Populate trading lessons for educational content'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate trading lessons...'))
        
        # Trading Basics Lessons
        basics_lessons = [
            {
                'title': 'What is Stock Trading?',
                'category': 'basics',
                'difficulty': 'beginner',
                'order_index': 1,
                'estimated_read_time': 5,
                'key_concepts': ['stocks', 'shares', 'ownership', 'market'],
                'content': """
# What is Stock Trading?

Stock trading is the buying and selling of shares in publicly traded companies. When you buy a stock, you're purchasing a small piece of ownership in that company.

## Key Concepts:
- **Stock**: A share in the ownership of a company
- **Share**: A unit of ownership in a corporation
- **Dividend**: Payment made by companies to shareholders
- **Market Cap**: Total value of a company's shares

## Why Trade Stocks?
1. **Potential for Growth**: Stocks can appreciate in value
2. **Dividend Income**: Some stocks pay regular dividends
3. **Liquidity**: Stocks can be bought and sold easily
4. **Inflation Hedge**: Stocks historically outpace inflation

Remember: This platform uses **virtual money** for practice - perfect for learning without risk!
                """,
                'recommended_practice': 'Start by exploring the stock list and watchlist features. Add 3-5 stocks to your watchlist and observe their price movements for a week.'
            },
            {
                'title': 'Order Types Explained',
                'category': 'basics',
                'difficulty': 'beginner',
                'order_index': 2,
                'estimated_read_time': 8,
                'key_concepts': ['market order', 'limit order', 'stop loss'],
                'content': """
# Order Types Explained

Understanding different order types is crucial for successful trading.

## Market Order
- **What**: Buy/sell immediately at current market price
- **When to use**: When you want to execute quickly
- **Risk**: Price may change between order placement and execution

## Limit Order
- **What**: Buy/sell only at specified price or better
- **When to use**: When you want price control
- **Risk**: Order may not execute if price doesn't reach your limit

## Stop Loss Order
- **What**: Sell automatically when price drops to specified level
- **When to use**: To limit losses on existing positions
- **Risk**: May execute at worse price in fast-moving markets

## Practice Exercise
Try placing different order types on this platform to see how they work!
                """,
                'recommended_practice': 'Practice placing all three order types with small amounts. Try setting a limit order below current market price and see if it executes.'
            },
        ]
        
        # Technical Analysis Lessons
        technical_lessons = [
            {
                'title': 'Introduction to Technical Analysis',
                'category': 'technical',
                'difficulty': 'beginner',
                'order_index': 1,
                'estimated_read_time': 10,
                'key_concepts': ['price action', 'charts', 'trends', 'support', 'resistance'],
                'content': """
# Introduction to Technical Analysis

Technical analysis studies price movements and patterns to predict future stock behavior.

## Core Principles:
1. **Price Reflects Everything**: All information is already in the stock price
2. **Prices Move in Trends**: Stocks tend to continue in their current direction
3. **History Repeats**: Similar patterns tend to occur repeatedly

## Key Tools:
- **Moving Averages**: Show average price over time periods
- **RSI**: Measures if stock is overbought or oversold (0-100 scale)
- **MACD**: Shows relationship between two moving averages
- **Support/Resistance**: Price levels where stock tends to bounce

## How to Use on This Platform:
Check the technical indicators section on stock detail pages to see real calculations for each stock.
                """,
                'recommended_practice': 'Look at technical indicators for 5 different stocks. Notice which ones are above/below their moving averages and compare RSI values.'
            },
            {
                'title': 'Understanding Moving Averages',
                'category': 'technical',
                'difficulty': 'beginner',
                'order_index': 2,
                'estimated_read_time': 12,
                'key_concepts': ['SMA', 'EMA', 'crossover', 'trend'],
                'content': """
# Understanding Moving Averages

Moving averages smooth out price data to identify trends more clearly.

## Simple Moving Average (SMA)
- Average of closing prices over X periods
- SMA 20 = average of last 20 days
- More stable, less sensitive to recent changes

## Exponential Moving Average (EMA)
- Gives more weight to recent prices
- More responsive to price changes
- Better for short-term trading

## Key Strategies:
- **Golden Cross**: When short MA crosses above long MA (bullish)
- **Death Cross**: When short MA crosses below long MA (bearish)
- **Price vs MA**: Price above MA suggests uptrend

## Practice on This Platform:
Our system calculates SMA 20, 50, 200 and EMA 12, 26 for each stock automatically!
                """,
                'recommended_practice': 'Find stocks where price is above SMA 20 but below SMA 50. These might be in short-term uptrends but longer-term downtrends.'
            },
        ]
        
        # Risk Management Lessons
        risk_lessons = [
            {
                'title': 'Position Sizing and Risk Management',
                'category': 'risk_management',
                'difficulty': 'intermediate',
                'order_index': 1,
                'estimated_read_time': 15,
                'key_concepts': ['position sizing', 'risk per trade', 'portfolio allocation'],
                'content': """
# Position Sizing and Risk Management

Proper risk management is the difference between long-term success and failure in trading.

## The 1% Rule
Never risk more than 1-2% of your account on a single trade:
- Account: $10,000
- Risk per trade: $100-200 maximum
- If stop loss is $2 away from entry, buy max 50-100 shares

## Position Sizing Formula:
**Shares = (Account × Risk%) ÷ (Entry Price - Stop Loss Price)**

## Diversification Rules:
- Don't put more than 5% in any single stock
- Spread across different sectors
- Never go "all in" on one trade

## Why This Matters:
With $10,000 virtual money, practice these rules as if it were real money!
                """,
                'recommended_practice': 'Calculate position sizes for your next 3 trades using the 1% rule. Practice setting appropriate stop losses.'
            },
        ]
        
        # Psychology Lessons
        psychology_lessons = [
            {
                'title': 'Trading Psychology and Emotions',
                'category': 'psychology',
                'difficulty': 'intermediate',
                'order_index': 1,
                'estimated_read_time': 12,
                'key_concepts': ['fear', 'greed', 'discipline', 'emotional control'],
                'content': """
# Trading Psychology and Emotions

Your mind is your most important trading tool - and your biggest enemy.

## Common Emotional Traps:
1. **Fear of Missing Out (FOMO)**: Jumping into trades too late
2. **Revenge Trading**: Trying to recover losses with bigger bets
3. **Overconfidence**: Taking excessive risks after wins
4. **Analysis Paralysis**: Overthinking and missing opportunities

## How to Combat Emotions:
- **Have a Plan**: Know entry, exit, and stop loss before entering
- **Keep a Journal**: Record why you made each trade
- **Start Small**: Use smaller positions while learning
- **Accept Losses**: They're part of trading

## Practice Benefits:
Simulation trading helps you experience these emotions without real money at risk. Pay attention to how you feel when trades go against you!
                """,
                'recommended_practice': 'Keep a trading journal for your next 10 trades. Write down your emotions before, during, and after each trade.'
            },
        ]
        
        all_lessons = basics_lessons + technical_lessons + risk_lessons + psychology_lessons
        
        created_count = 0
        for lesson_data in all_lessons:
            lesson, created = TradingLesson.objects.get_or_create(
                title=lesson_data['title'],
                category=lesson_data['category'],
                defaults=lesson_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created lesson: {lesson.title}")
            else:
                self.stdout.write(f"Lesson already exists: {lesson.title}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new lessons!')
        )