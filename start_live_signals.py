"""
Quick script to start sending live signals with comprehensive analysis
"""
import asyncio
import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.main import MemeBot
from src.config import (
    TELEGRAM_BOT_TOKEN, SIGNAL_CHANNEL_ID, PERFORMANCE_CHANNEL_ID, 
    SCAN_INTERVAL_MINUTES, CHAIN_ID, BOT_MODE, PAPER_TRADING, PAPER_STARTING_SOL
)

async def start_live_signals():
    """Start live signal discovery and sending with comprehensive analysis"""
    
    # print(f"Using Chain ID: {CHAIN_ID}")
    # print(f"Bot Mode: {BOT_MODE}")
    # print(f"Scan Interval: {SCAN_INTERVAL_MINUTES} minutes")
    # print(f"Database: {os.getenv('DB_USER', 'root')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'meme_trading_bot')}")
    
    print("🚀 Starting Live Meme Trading Signal Bot...")
    print("="*60)
    
    # PRODUCTION MODE: Analyze all tokens for live signals
    DEBUG_MODE = False
    DEBUG_TOKEN_LIMIT = 3  # Only used when DEBUG_MODE = True

    # Parse PAPER_TRADING and PAPER_STARTING_SOL to correct types
    paper_trading_env = PAPER_TRADING if isinstance(PAPER_TRADING, str) else str(PAPER_TRADING)
    paper_trading = paper_trading_env.lower() in ("true", "1", "yes")
    try:
        starting_sol = float(PAPER_STARTING_SOL)
    except Exception:
        starting_sol = 10.0

    # Initialize bot
    bot = MemeBot(TELEGRAM_BOT_TOKEN, SIGNAL_CHANNEL_ID, paper_trading, starting_sol)
    
    # Show current configuration
    # print("📊 Getting configuration summary...")
    # config_summary = bot.get_config_summary()
    # print(config_summary)
    
    print("✅ All systems ready! Starting live signal scanning...")
    print(f"💡 Bot will scan for new signals every {SCAN_INTERVAL_MINUTES} minutes")
    # print("📊 Performance tracking is active")
    # print("🔄 Press Ctrl+C to stop\n")
    
    # Choose execution mode based on configuration
    if BOT_MODE.lower() == "continuous":
        # Use the built-in continuous mode
        await bot.run_continuous_async(SCAN_INTERVAL_MINUTES)
    else:
        # Use simple loop for single/manual mode
        signal_count = 0
        
        try:
            while True:
                try:
                    print(f"🔍 Scanning for signals... (Signal #{signal_count + 1})")
                    
                    # Use the comprehensive analysis from main bot
                    signals = await bot.scan_and_analyze()
                    
                    if signals:
                        print(f"🎯 Sent {len(signals)} quality signals")
                        signal_count += len(signals)
                    else:
                        print("🎯 Sent 0 quality signals")
                    
                    print(f"⏰ Waiting {SCAN_INTERVAL_MINUTES} minutes for next scan...")
                    await asyncio.sleep(SCAN_INTERVAL_MINUTES * 60)  # Configurable interval
                    
                except Exception as e:
                    print(f"❌ Error during scan: {e}")
                    print("⏰ Waiting 5 minutes before retry...")
                    await asyncio.sleep(300)  # 5 minutes on error
                    
        except KeyboardInterrupt:
            print("\n⏹️ Bot stopped by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(start_live_signals())
