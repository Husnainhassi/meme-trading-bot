from dotenv import load_dotenv
import os

# Load environment variables from .env file in project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Blockchain configuration
CHAIN_ID = os.getenv("CHAIN_ID", "solana")

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SIGNAL_CHANNEL_ID = os.getenv('SIGNAL_CHANNEL_ID', '')  # Main signal channel
PERFORMANCE_CHANNEL_ID = os.getenv('PERFORMANCE_CHANNEL_ID', '')  # Performance tracking channel

# MySQL Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "meme_trading_bot")

# Bot configuration - OPTIMIZED FOR MEME COIN SPEED AND VOLATILITY
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "5"))   # Every 5 minutes - memes move FAST
BOT_MODE = os.getenv("BOT_MODE", "continuous")  # Continuous scanning essential for catching pumps

# Trading thresholds - MEME COIN OPTIMIZED PARAMETERS
MIN_BOOM_SCORE = float(os.getenv("MIN_BOOM_SCORE", "20"))  # Lower threshold - catch early momentum
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "1000"))  # Ultra-low for early detection
MAX_RISK_SCORE = float(os.getenv("MAX_RISK_SCORE", "90"))  # High tolerance - memes are inherently risky

# Comprehensive Scoring Thresholds - CALIBRATED FOR MEME ECOSYSTEM
TIER_A_THRESHOLD = float(os.getenv("TIER_A_THRESHOLD", "40"))  # Premium meme coins with strong signals
TIER_B_THRESHOLD = float(os.getenv("TIER_B_THRESHOLD", "25"))  # Good momentum candidates  
TIER_C_THRESHOLD = float(os.getenv("TIER_C_THRESHOLD", "15"))  # Early speculation plays

# Signal Generation Criteria - FAST REACTION TO MEME TRENDS
TIER_A_ALWAYS_SIGNAL = os.getenv("TIER_A_ALWAYS_SIGNAL", "true").lower() == "true"
TIER_B_MIN_SCORE = float(os.getenv("TIER_B_MIN_SCORE", "30"))  # Signal strong B-tier quickly
TIER_C_MIN_SCORE = float(os.getenv("TIER_C_MIN_SCORE", "18"))  # Signal promising C-tier early
TIER_D_NEVER_SIGNAL = os.getenv("TIER_D_NEVER_SIGNAL", "true").lower() == "true"

# Paper Trading Configuration - USD BASED SYSTEM
PAPER_TRADING = os.getenv("PAPER_TRADING", "false").lower() == "true"
PAPER_STARTING_USD_BALANCE = float(os.getenv("PAPER_STARTING_USD_BALANCE", "10000"))  # $10,000 starting balance
PAPER_TRADE_AMOUNT_USD = float(os.getenv("PAPER_TRADE_AMOUNT_USD", "25"))  # $25 per trade

# Price Target Configuration - REALISTIC MEME COIN DYNAMICS
# Based on ACTUAL DexScreener trending data - meme coins regularly hit 100-2000%+ gains
TIER_A_TARGET_1_PERCENT = float(os.getenv("TIER_A_TARGET_1_PERCENT", "200"))   # +200% (Conservative for A-tier memes)
TIER_A_TARGET_2_PERCENT = float(os.getenv("TIER_A_TARGET_2_PERCENT", "1000"))  # +1000% (Strong memes regularly hit this)
TIER_A_STOP_LOSS_PERCENT = float(os.getenv("TIER_A_STOP_LOSS_PERCENT", "-50"))  # -50% (Memes are volatile, need room)

TIER_B_TARGET_1_PERCENT = float(os.getenv("TIER_B_TARGET_1_PERCENT", "100"))   # +100% (Decent memes can 2x easily)
TIER_B_TARGET_2_PERCENT = float(os.getenv("TIER_B_TARGET_2_PERCENT", "500"))   # +500% (Strong B-tier can pump hard)
TIER_B_STOP_LOSS_PERCENT = float(os.getenv("TIER_B_STOP_LOSS_PERCENT", "-60"))  # -60% (Higher risk tolerance needed)

TIER_C_TARGET_1_PERCENT = float(os.getenv("TIER_C_TARGET_1_PERCENT", "50"))    # +50% (Quick gains on momentum)
TIER_C_TARGET_2_PERCENT = float(os.getenv("TIER_C_TARGET_2_PERCENT", "200"))   # +200% (Even C-tier can pump)
TIER_C_STOP_LOSS_PERCENT = float(os.getenv("TIER_C_STOP_LOSS_PERCENT", "-70"))  # -70% (Speculative plays need wide stops)

# Enhanced Data Sources
BIRDEYE_API_KEY = os.getenv('BIRDEYE_API_KEY', 'ab0cf99f228349ab947bcd56fdf33e0d')  # Get from birdeye.so
DEXTOOLS_API_KEY = os.getenv('DEXTOOLS_API_KEY', '')  # Get from dextools.io
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')  # Optional for CoinGecko Pro
ENABLE_AUTO_TRACKING = True  # Automatically track all signals

# Paper trading mode
PAPER_TRADING = os.getenv("PAPER_TRADING", True)
PAPER_STARTING_SOL = os.getenv("PAPER_STARTING_SOL", 100.0)  # Starting SOL for paper trading

# Data Source Priorities (1 = highest priority)
DATA_SOURCE_PRIORITIES = {
    'birdeye': 1,      # Most reliable for real-time data
    'dextools': 2,     # Good for analytics  
    'dexscreener': 3,  # Good for discovery
    'coingecko': 4     # Good for market cap data
}

print(f"Using Chain ID: {CHAIN_ID}")
print(f"Bot Mode: {BOT_MODE}")
print(f"Scan Interval: {SCAN_INTERVAL_MINUTES} minutes")
print(f"Database: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")