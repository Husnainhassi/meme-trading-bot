#!/usr/bin/env python3
"""
Paper Trading Performance Analysis Script
Analyzes 15+ days of paper trading performance from MySQL database
"""

import sys
import os
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

def get_db_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return connection
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def analyze_paper_trading_performance():
    """Comprehensive paper trading performance analysis"""
    
    print("🔍 PAPER TRADING PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    connection = get_db_connection()
    if not connection:
        print("❌ Could not connect to database")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 1. Database Tables Check
        print("\n📋 DATABASE TABLES:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            table_name = list(table.values())[0]
            print(f"  ✅ {table_name}")
        
        # 2. Overall Paper Trading Summary (Last 20 Days)
        print("\n📊 PAPER TRADING SUMMARY (Last 20 Days):")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(amount_usd) as total_invested,
                SUM(CASE WHEN profit_loss_usd IS NOT NULL THEN profit_loss_usd ELSE 0 END) as total_pnl,
                AVG(CASE WHEN profit_loss_usd IS NOT NULL THEN profit_loss_usd ELSE 0 END) as avg_pnl,
                SUM(CASE WHEN profit_loss_usd > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss_usd < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(CASE WHEN profit_loss_usd IS NULL THEN 1 ELSE 0 END) as open_trades,
                MAX(profit_loss_usd) as best_trade,
                MIN(profit_loss_usd) as worst_trade
            FROM paper_trades 
            WHERE buy_timestamp >= DATE_SUB(NOW(), INTERVAL 20 DAY)
        """)
        
        summary = cursor.fetchone()
        if summary and summary['total_trades'] > 0:
            total = summary['total_trades']
            invested = summary['total_invested'] or 0
            pnl = summary['total_pnl'] or 0
            wins = summary['winning_trades'] or 0
            losses = summary['losing_trades'] or 0
            open_trades = summary['open_trades'] or 0
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            
            print(f"  💰 Total Trades: {total}")
            print(f"  💵 Total Invested: ${invested:.2f}")
            print(f"  📈 Total P&L: ${pnl:.2f}")
            print(f"  🎯 Win Rate: {win_rate:.1f}% ({wins} wins, {losses} losses)")
            print(f"  📊 Open Positions: {open_trades}")
            print(f"  🚀 Best Trade: ${summary['best_trade']:.2f}" if summary['best_trade'] else "  🚀 Best Trade: N/A")
            print(f"  📉 Worst Trade: ${summary['worst_trade']:.2f}" if summary['worst_trade'] else "  📉 Worst Trade: N/A")
        else:
            print("  ❌ No paper trades found in last 20 days")
        
        # 3. Daily Activity Pattern
        print("\n📅 DAILY TRADING ACTIVITY:")
        cursor.execute("""
            SELECT 
                DATE(buy_timestamp) as trade_date,
                COUNT(*) as trades_count,
                SUM(amount_usd) as daily_invested,
                SUM(CASE WHEN profit_loss_usd IS NOT NULL THEN profit_loss_usd ELSE 0 END) as daily_pnl,
                AVG(CASE WHEN profit_loss_usd IS NOT NULL THEN profit_loss_usd ELSE 0 END) as avg_trade_pnl
            FROM paper_trades 
            WHERE buy_timestamp >= DATE_SUB(NOW(), INTERVAL 20 DAY)
            GROUP BY DATE(buy_timestamp)
            ORDER BY trade_date DESC
            LIMIT 10
        """)
        
        daily_data = cursor.fetchall()
        if daily_data:
            for day in daily_data:
                date = day['trade_date']
                count = day['trades_count']
                invested = day['daily_invested'] or 0
                pnl = day['daily_pnl'] or 0
                print(f"  {date}: {count} trades | Invested: ${invested:.2f} | P&L: ${pnl:.2f}")
        else:
            print("  ❌ No daily activity data found")
        
        # 4. Recent Trades (Last 15)
        print("\n📋 RECENT PAPER TRADES (Last 15):")
        cursor.execute("""
            SELECT 
                token_symbol,
                SUBSTRING(token_address, 1, 8) as short_address,
                ROUND(buy_price_usd, 8) as buy_price,
                amount_usd,
                ROUND(profit_loss_usd, 2) as pnl,
                ROUND(((last_price_usd - buy_price_usd) / buy_price_usd * 100), 2) as pnl_pct,
                buy_timestamp,
                status
            FROM paper_trades 
            ORDER BY buy_timestamp DESC 
            LIMIT 15
        """)
        
        recent_trades = cursor.fetchall()
        if recent_trades:
            print("  Date Time          | Token     | Buy Price    | Amount | P&L    | %     | Status")
            print("  " + "-" * 80)
            for trade in recent_trades:
                symbol = trade['token_symbol'] or 'UNKNOWN'
                addr = trade['short_address'] + '...'
                buy_price = trade['buy_price']
                amount = trade['amount_usd']
                pnl = trade['pnl'] if trade['pnl'] is not None else 0
                pnl_pct = trade['pnl_pct'] if trade['pnl_pct'] is not None else 0
                timestamp = trade['buy_timestamp']
                status = trade['status']
                
                pnl_color = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                print(f"  {timestamp} | {symbol:8} | ${buy_price:.8f} | ${amount:5.2f} | {pnl_color}${pnl:6.2f} | {pnl_pct:5.1f}% | {status}")
        else:
            print("  ❌ No recent trades found")
        
        # 5. Best Performing Trades
        print("\n🚀 TOP 10 BEST PERFORMING TRADES:")
        cursor.execute("""
            SELECT 
                token_symbol,
                SUBSTRING(token_address, 1, 8) as short_address,
                ROUND(buy_price_usd, 8) as buy_price,
                ROUND(last_price_usd, 8) as current_price,
                amount_usd,
                ROUND(profit_loss_usd, 2) as pnl,
                ROUND(((last_price_usd - buy_price_usd) / buy_price_usd * 100), 2) as pnl_pct,
                buy_timestamp
            FROM paper_trades 
            WHERE profit_loss_usd IS NOT NULL AND profit_loss_usd > 0
            ORDER BY profit_loss_usd DESC 
            LIMIT 10
        """)
        
        best_trades = cursor.fetchall()
        if best_trades:
            for i, trade in enumerate(best_trades, 1):
                symbol = trade['token_symbol'] or 'UNKNOWN'
                pnl = trade['pnl']
                pnl_pct = trade['pnl_pct']
                amount = trade['amount_usd']
                timestamp = trade['buy_timestamp']
                print(f"  {i:2}. {symbol:8} | ${pnl:7.2f} (+{pnl_pct:6.1f}%) | ${amount:.2f} invested | {timestamp}")
        else:
            print("  ❌ No profitable trades found")
        
        # 6. Worst Performing Trades
        print("\n📉 TOP 10 WORST PERFORMING TRADES:")
        cursor.execute("""
            SELECT 
                token_symbol,
                SUBSTRING(token_address, 1, 8) as short_address,
                ROUND(buy_price_usd, 8) as buy_price,
                ROUND(last_price_usd, 8) as current_price,
                amount_usd,
                ROUND(profit_loss_usd, 2) as pnl,
                ROUND(((last_price_usd - buy_price_usd) / buy_price_usd * 100), 2) as pnl_pct,
                buy_timestamp
            FROM paper_trades 
            WHERE profit_loss_usd IS NOT NULL AND profit_loss_usd < 0
            ORDER BY profit_loss_usd ASC 
            LIMIT 10
        """)
        
        worst_trades = cursor.fetchall()
        if worst_trades:
            for i, trade in enumerate(worst_trades, 1):
                symbol = trade['token_symbol'] or 'UNKNOWN'
                pnl = trade['pnl']
                pnl_pct = trade['pnl_pct']
                amount = trade['amount_usd']
                timestamp = trade['buy_timestamp']
                print(f"  {i:2}. {symbol:8} | ${pnl:7.2f} ({pnl_pct:6.1f}%) | ${amount:.2f} invested | {timestamp}")
        else:
            print("  ✅ No losing trades found")
        
        # 7. Current Open Positions
        print("\n🔄 CURRENT OPEN POSITIONS:")
        cursor.execute("""
            SELECT 
                token_symbol,
                SUBSTRING(token_address, 1, 8) as short_address,
                ROUND(buy_price_usd, 8) as buy_price,
                amount_usd,
                tokens_bought,
                DATEDIFF(NOW(), buy_timestamp) as days_held,
                buy_timestamp
            FROM paper_trades 
            WHERE status = 'OPEN'
            ORDER BY buy_timestamp DESC
        """)
        
        open_positions = cursor.fetchall()
        if open_positions:
            print("  Token     | Address   | Buy Price    | Amount | Days Held | Buy Date")
            print("  " + "-" * 70)
            for pos in open_positions:
                symbol = pos['token_symbol'] or 'UNKNOWN'
                addr = pos['short_address'] + '...'
                buy_price = pos['buy_price']
                amount = pos['amount_usd']
                days = pos['days_held']
                timestamp = pos['buy_timestamp']
                print(f"  {symbol:8} | {addr:8} | ${buy_price:.8f} | ${amount:5.2f} | {days:8} | {timestamp}")
        else:
            print("  ✅ No open positions")
        
        # 8. Recent Bot Activity Check
        print("\n🤖 RECENT BOT ACTIVITY (Last 7 Days):")
        cursor.execute("""
            SELECT 
                DATE(created_at) as signal_date,
                COUNT(*) as signals_generated,
                MAX(created_at) as last_signal_time
            FROM signals 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY signal_date DESC
        """)
        
        activity = cursor.fetchall()
        if activity:
            for day in activity:
                date = day['signal_date']
                count = day['signals_generated']
                last = day['last_signal_time']
                print(f"  {date}: {count} signals generated | Last: {last}")
        else:
            print("  ⚠️ No bot activity in last 7 days")
        
        print("\n" + "=" * 50)
        print("✅ Analysis Complete!")
        
    except Error as e:
        print(f"❌ Database query error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    analyze_paper_trading_performance()
