#!/usr/bin/env python3
"""
Price Tracker - Track paper trade performance over time
Records price changes at regular intervals to determine optimal exit timing
"""

import mysql.connector
from mysql.connector import Error
import requests
import time
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

class PriceTracker:
    def __init__(self):
        self.db_config = {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'database': DB_NAME
        }
        self.create_price_history_table()
    
    def connect_to_database(self):
        """Connect to the database"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except Error as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def create_price_history_table(self):
        """Create table to track price changes over time"""
        connection = self.connect_to_database()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                paper_trade_id INT NOT NULL,
                token_address VARCHAR(255) NOT NULL,
                token_symbol VARCHAR(50),
                price_usd DECIMAL(20,8) NOT NULL,
                performance_pct DECIMAL(10,4),
                profit_loss_usd DECIMAL(20,8),
                minutes_since_entry INT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_paper_trade_id (paper_trade_id),
                INDEX idx_token_address (token_address),
                INDEX idx_recorded_at (recorded_at),
                FOREIGN KEY (paper_trade_id) REFERENCES paper_trades(id) ON DELETE CASCADE
            );
            """
            
            cursor.execute(create_table_query)
            connection.commit()
            print("✅ Price history table created/verified")
            
        except Error as e:
            print(f"❌ Error creating price history table: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_token_price(self, token_address):
        """Get current token price from DexScreener"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    # Get the pair with highest liquidity
                    pairs = data['pairs']
                    best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
                    return float(best_pair['priceUsd'])
            
            return None
        except Exception as e:
            print(f"❌ Error fetching price for {token_address}: {e}")
            return None
    
    def record_price_snapshot(self):
        """Record current prices for all open paper trades"""
        connection = self.connect_to_database()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            # Get all open paper trades
            cursor.execute("""
                SELECT id, token_address, token_symbol, buy_price_usd, amount_usd, buy_timestamp
                FROM paper_trades 
                WHERE status = 'OPEN'
            """)
            
            open_trades = cursor.fetchall()
            snapshots_recorded = 0
            
            for trade in open_trades:
                trade_id, token_address, token_symbol, buy_price_usd, amount_usd, buy_timestamp = trade
                
                # Get current price
                current_price = self.get_token_price(token_address)
                if not current_price:
                    continue
                
                # Calculate performance
                buy_price_float = float(buy_price_usd)
                amount_usd_float = float(amount_usd)
                performance_pct = ((current_price - buy_price_float) / buy_price_float) * 100
                profit_loss_usd = (current_price - buy_price_float) * (amount_usd_float / buy_price_float)
                
                # Calculate minutes since entry
                minutes_since_entry = int((datetime.now() - buy_timestamp).total_seconds() / 60)
                
                # Insert price snapshot
                insert_query = """
                INSERT INTO price_history 
                (paper_trade_id, token_address, token_symbol, price_usd, performance_pct, 
                 profit_loss_usd, minutes_since_entry)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    trade_id, token_address, token_symbol, current_price,
                    performance_pct, profit_loss_usd, minutes_since_entry
                ))
                
                snapshots_recorded += 1
                print(f"📊 {token_symbol}: {performance_pct:.2f}% ({minutes_since_entry}m)")
            
            connection.commit()
            print(f"✅ Recorded {snapshots_recorded} price snapshots")
            
        except Error as e:
            print(f"❌ Error recording price snapshots: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def analyze_timing_patterns(self):
        """Analyze when tokens typically pump or dump"""
        connection = self.connect_to_database()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            # Analyze performance by time intervals
            query = """
            SELECT 
                CASE 
                    WHEN minutes_since_entry <= 15 THEN '0-15 min'
                    WHEN minutes_since_entry <= 30 THEN '15-30 min'
                    WHEN minutes_since_entry <= 60 THEN '30-60 min'
                    WHEN minutes_since_entry <= 120 THEN '1-2 hours'
                    WHEN minutes_since_entry <= 360 THEN '2-6 hours'
                    WHEN minutes_since_entry <= 1440 THEN '6-24 hours'
                    ELSE '24+ hours'
                END as time_interval,
                COUNT(*) as snapshots,
                AVG(performance_pct) as avg_performance,
                MAX(performance_pct) as max_performance,
                MIN(performance_pct) as min_performance,
                SUM(CASE WHEN performance_pct > 10 THEN 1 ELSE 0 END) as pumps_10pct,
                SUM(CASE WHEN performance_pct > 50 THEN 1 ELSE 0 END) as pumps_50pct,
                SUM(CASE WHEN performance_pct > 100 THEN 1 ELSE 0 END) as moons_100pct
            FROM price_history
            GROUP BY time_interval
            ORDER BY 
                CASE time_interval
                    WHEN '0-15 min' THEN 1
                    WHEN '15-30 min' THEN 2
                    WHEN '30-60 min' THEN 3
                    WHEN '1-2 hours' THEN 4
                    WHEN '2-6 hours' THEN 5
                    WHEN '6-24 hours' THEN 6
                    WHEN '24+ hours' THEN 7
                END
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Prepare analysis output
            analysis_output = []
            analysis_output.append(f"\n🎯 TIMING PATTERN ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            analysis_output.append("=" * 80)
            
            for row in results:
                interval, snapshots, avg_perf, max_perf, min_perf, pumps_10, pumps_50, moons = row
                pump_rate_10 = (pumps_10 / snapshots * 100) if snapshots > 0 else 0
                pump_rate_50 = (pumps_50 / snapshots * 100) if snapshots > 0 else 0
                moon_rate = (moons / snapshots * 100) if snapshots > 0 else 0
                
                analysis_output.append(f"⏰ {interval}:")
                analysis_output.append(f"   📊 Snapshots: {snapshots}")
                analysis_output.append(f"   📈 Avg Performance: {avg_perf:.2f}%")
                analysis_output.append(f"   🚀 Max Pump: {max_perf:.2f}%")
                analysis_output.append(f"   📉 Max Dump: {min_perf:.2f}%")
                analysis_output.append(f"   🎯 10%+ Pumps: {pump_rate_10:.1f}% ({pumps_10}/{snapshots})")
                analysis_output.append(f"   🚀 50%+ Pumps: {pump_rate_50:.1f}% ({pumps_50}/{snapshots})")
                analysis_output.append(f"   🌙 100%+ Moons: {moon_rate:.1f}% ({moons}/{snapshots})")
                analysis_output.append("-" * 80)
            
            # Print to console (goes to main log)
            for line in analysis_output:
                print(line)
            
            # Also write to separate timing analysis log
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            timing_log_path = os.path.join(log_dir, 'timing_analysis.log')
            with open(timing_log_path, 'a', encoding='utf-8') as f:
                for line in analysis_output:
                    f.write(line + '\n')
                f.write('\n')
            
        except Error as e:
            print(f"❌ Error analyzing timing patterns: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def main():
    """Main function"""
    print("🔍 PRICE TRACKER - Recording Performance Over Time")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tracker = PriceTracker()
    
    # Record current price snapshots
    tracker.record_price_snapshot()
    
    # Analyze timing patterns if we have data
    tracker.analyze_timing_patterns()
    
    print("\n✅ Price tracking complete!")

if __name__ == "__main__":
    main()
