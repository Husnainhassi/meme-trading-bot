"""
Database module for storing processed tokens and analysis results.
Uses MySQL for robust data storage with XAMPP.
"""

import mysql.connector
from mysql.connector import Error
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


class TokenDatabase:

    def __init__(self):
        """
        Initialize database connection.
        """
        self.connection_config = {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'database': DB_NAME,
            'autocommit': True,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        self.init_database()
    
    def get_connection(self):
        """Get a fresh database connection."""
        try:
            connection = mysql.connector.connect(**self.connection_config)
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist."""
        try:
            # Connect without specifying database
            temp_config = self.connection_config.copy()
            temp_config.pop('database', None)
            
            connection = mysql.connector.connect(**temp_config)
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            # print(f"✅ Database '{DB_NAME}' ready")
            
            cursor.close()
            connection.close()
            return True
            
        except Error as e:
            print(f"Error creating database: {e}")
            return False
    
    def init_database(self):
        """Create database and tables if they don't exist."""
        # First, create the database
        if not self.create_database_if_not_exists():
            return
        
        connection = self.get_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            
            # Signals table - stores trading signals sent
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    token_address VARCHAR(255) NOT NULL,
                    signal_type VARCHAR(20) NOT NULL,
                    boom_score DECIMAL(5, 2) NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    current_price DECIMAL(20, 8),
                    entry_target DECIMAL(20, 8),
                    take_profit_1 DECIMAL(20, 8),
                    take_profit_2 DECIMAL(20, 8),
                    stop_loss DECIMAL(20, 8),
                    telegram_sent BOOLEAN DEFAULT FALSE,
                    sent_timestamp TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_signals_token (token_address),
                    INDEX idx_signal_type (signal_type),
                    INDEX idx_telegram_sent (telegram_sent)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    token_address VARCHAR(255) NOT NULL,
                    token_symbol VARCHAR(50),
                    buy_price_usd DECIMAL(20, 8) NOT NULL,
                    amount_usd DECIMAL(20, 8) NOT NULL,
                    tokens_bought DECIMAL(30, 8) NOT NULL,
                    buy_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'OPEN',
                    last_checked TIMESTAMP NULL,
                    last_price_usd DECIMAL(20, 8) DEFAULT NULL,
                    profit_loss_usd DECIMAL(20, 8) DEFAULT NULL,
                    performance_note TEXT,
                    INDEX idx_token_address (token_address),
                    INDEX idx_status (status),
                    UNIQUE KEY unique_token_address (token_address)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            cursor.close()
            # print("✅ Database tables initialized successfully")
            
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            if connection.is_connected():
                connection.close()

    def store_signal(self, token_address: str, signal_type: str, boom_score: float,
                    risk_level: str, targets: Optional[Dict] = None) -> bool:
        """
        Store trading signal.
        
        Args:
            token_address: The token mint address
            signal_type: Type of signal ('BUY', 'SELL', 'MONITOR')
            boom_score: Boom probability score
            risk_level: Risk assessment level
            targets: Optional price targets
            
        Returns:
            Boolean indicating success
        """
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            current_price = targets.get('current_price') if targets else None
            entry_target = targets.get('entry_target') if targets else None
            take_profit_1 = targets.get('take_profit_1') if targets else None
            take_profit_2 = targets.get('take_profit_2') if targets else None
            stop_loss = targets.get('stop_loss') if targets else None
            telegram_sent = True  # Default to not sent
            sent_timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO signals 
                (token_address, signal_type, boom_score, risk_level, current_price,
                 entry_target, take_profit_1, take_profit_2, stop_loss, telegram_sent, sent_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                token_address, signal_type, boom_score, risk_level, current_price,
                entry_target, take_profit_1, take_profit_2, stop_loss, telegram_sent, sent_timestamp
            ))
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"Database error storing signal for {token_address}: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()
        
    def get_paper_trade_by_address(self, token_address: str) -> Optional[Dict]:
        """
        Check if a paper trade already exists for this token address.
        Args:
            token_address: Token address to check
        Returns:
            Dict of existing trade or None
        """
        connection = self.get_connection()
        if not connection:
            return None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM paper_trades WHERE token_address = %s AND status = 'OPEN' LIMIT 1
            """, (token_address,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            print(f"Database error checking existing trade for {token_address}: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
                
    def store_paper_trade(self, token_address: str, token_symbol: str, buy_price_usd: float, amount_usd: float, tokens_bought: float, timestamp: str) -> bool:
        """
        Store a new paper trade in the database.
        Args:
            token_address: Token address
            token_symbol: Symbol
            buy_price_usd: Price in USD at buy
            amount_usd: Amount spent in USD
            tokens_bought: Number of tokens purchased
            timestamp: ISO timestamp
        Returns:
            Boolean indicating success
        """
        connection = self.get_connection()
        if not connection:
            return False
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO paper_trades (token_address, token_symbol, buy_price_usd, amount_usd, tokens_bought, buy_timestamp, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'OPEN')
            """, (token_address, token_symbol, buy_price_usd, amount_usd, tokens_bought, timestamp))
            cursor.close()
            return True
        except Error as e:
            print(f"Database error storing paper trade for {token_address}: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()

    def get_open_paper_trades(self) -> List[Dict]:
        """
        Fetch all open paper trades for performance monitoring.
        Returns:
            List of open paper trade dicts
        """
        connection = self.get_connection()
        if not connection:
            return []
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY buy_timestamp ASC
            """)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Database error fetching open paper trades: {e}")
            return []
        finally:
            if connection.is_connected():
                connection.close()

    def update_paper_trade_performance(self, trade_id: int, last_price_usd: float, profit_loss_usd: float, note: str = None) -> bool:
        """
        Update a paper trade with latest price and P/L.
        Args:
            trade_id: Paper trade ID
            last_price_usd: Latest price in USD
            profit_loss_usd: P/L in USD
            note: Optional performance note
        Returns:
            Boolean indicating success
        """
        connection = self.get_connection()
        if not connection:
            return False
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE paper_trades SET last_checked = NOW(), last_price_usd = %s, profit_loss_usd = %s, performance_note = %s WHERE id = %s
            """, (last_price_usd, profit_loss_usd, note, trade_id))
            cursor.close()
            return True
        except Error as e:
            print(f"Database error updating paper trade {trade_id}: {e}")
            return False
        finally:
            if connection.is_connected():
                connection.close()
                
    def validate_connection(self) -> bool:
        """Validate the database connection."""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                print("✅ MySQL database connection successful")
                return True
            except Error as e:
                print(f"❌ Database connection test failed: {e}")
                return False
            finally:
                connection.close()
        else:
            print("❌ Could not establish database connection")
            return False


def get_database() -> TokenDatabase:
    """Get a database instance."""
    return TokenDatabase()


if __name__ == "__main__":
    # Test the database
    print("🗄️ Testing MySQL Token Database...")
    
    db = TokenDatabase()
    
    # Test connection
    if not db.validate_connection():
        print("❌ Database connection failed. Please check your XAMPP MySQL service.")
        exit(1)
