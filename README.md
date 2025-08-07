# 🚀 Meme Coin Trading Bot

A sophisticated Python-based trading bot that discovers, analyzes, and signals potential meme coin opportunities on Solana using **comprehensive research-backed evaluation framework** with **real data validation**.

## 🎯 Overview

This bot combines traditional technical analysis with an advanced **multi-dimensional scoring system** based on extensive research from successful crypto traders, YouTube analysis, Reddit communities, and proven on-chain patterns. It identifies high-potential meme coins with realistic return possibilities while systematically filtering out scams and rug pulls using **real market data**.

## ✨ Key Features

- **🎯 Comprehensive Evaluation Framework**: Research-backed 100-point scoring system across 6 categories
- **🔍 Real Data Validation**: Extracts actual social links, transaction counts, and community metrics from DexScreener
- **🚫 Fake Data Detection**: Removed all fabricated metrics - only uses real API data
- **🛡️ Advanced Security Screening**: Honeypot detection, contract analysis, and rug pull prevention
- **📱 Dual Telegram Channels**: Separate channels for signals and performance tracking
- **⚡ Real-time Performance Tracking**: Tracks signal performance at 1h, 4h, 12h, 24h intervals
- **🗄️ Enterprise Database**: MySQL storage with data quality tracking
- **🤖 Automated Discovery**: Continuous scanning with realistic signal filtering
- **⚙️ Fully Configurable**: All parameters adjustable via environment variables

## 🚀 Quick Start

### 1. **Setup Configuration**
```bash
# Copy configuration template
copy CONFIGURATION_TEMPLATE.env .env

# Edit .env with your API keys and preferences
notepad .env
```

### 2. **Key Configuration Options** ⚠️ **UPDATED REALISTIC THRESHOLDS**
```env
# ADJUSTED FOR REALISTIC MEME COIN SCORES
TIER_A_THRESHOLD=50          # Strong buy signals (was 80)
TIER_B_THRESHOLD=30          # Monitor signals (was 65)
TIER_C_THRESHOLD=20          # Watch list (was 50)

# Signal generation thresholds
TIER_B_MIN_SCORE=40          # Signal good B-tier tokens (was 70)
TIER_C_MIN_SCORE=25          # Signal decent C-tier tokens (was 60)
MIN_BOOM_SCORE=40           # Overall minimum score (was 50)

# Customize scanning
SCAN_INTERVAL_MINUTES=30     # Scan frequency
BOT_MODE=continuous          # Operation mode

# Set price targets per tier
TIER_A_TARGET_1_PERCENT=100  # A-tier: +100%/+300%
TIER_B_TARGET_1_PERCENT=75   # B-tier: +75%/+200%
TIER_C_TARGET_1_PERCENT=50   # C-tier: +50%/+150%
```

### 3. **Start Bot**
```bash
python start_live_signals.py
```

**📖 Complete Setup Guide**: See `COMPLETE_BOT_GUIDE.md` for detailed documentation.

## 📊 Comprehensive Scoring Framework

### 🎯 6-Category Evaluation System (100 Points Total)

#### 1. On-Chain Health & Security (25 Points)
- **Liquidity Pool Analysis**: Lock status, size, LP burn verification
- **Smart Contract Security**: Verification, honeypot checks, ownership status  
- **Token Distribution**: Holder concentration, developer allocation

#### 2. Market Dynamics & Trading (20 Points)
- **Volume & Activity**: Volume/MC ratio, transaction count, holder growth
- **Price Action Patterns**: Trend analysis, volatility assessment, support/resistance
- **Market Cap Positioning**: Optimal size range, age factor analysis

#### 3. Community & Social Signals (20 Points)
- **Community Strength**: Telegram, Twitter, Discord, Reddit presence
- **Narrative & Meme Power**: Viral potential, cultural relevance, originality

#### 4. Technical Foundation (15 Points)
- **Project Foundation**: Website, documentation, roadmap quality
- **Utility & Use Cases**: Real utility potential, ecosystem integration
- **Development Activity**: GitHub activity, update frequency

#### 5. Timing & Market Context (10 Points)
- **Market Timing**: Crypto sentiment, meme cycle position, catalysts
- **Discovery Timing**: Exchange listing status, influencer coverage

#### 6. Risk Assessment (10 Points - Deduction System)
- **Critical Red Flags**: Auto-disqualify conditions
- **Warning Signals**: Point deductions for suspicious patterns

### 🏆 Tier Classification ⚠️ **UPDATED FOR REALISTIC MEME COIN SCORING**

- **A-Tier (50-100 pts)**: Strong Buy - Exceptional potential with solid fundamentals *(was 80-100)*
- **B-Tier (30-49 pts)**: Monitor/Small Position - Good potential, moderate risk *(was 65-79)*
- **C-Tier (20-29 pts)**: Watch List - Mixed signals, speculation only *(was 50-64)*
- **D-Tier (<20 pts)**: Avoid - Multiple red flags or weak fundamentals *(unchanged)*

**📊 Realistic Scoring Context:**
- Most new meme coins score 25-45 points due to lack of established metrics
- Scores 40+ indicate strong potential relative to typical meme coin standards
- Scores 50+ are exceptional and rare - indicating serious long-term potential

*All tier thresholds are configurable via environment variables*

### ⚙️ Configuration Flexibility

**Strategy Examples:**
- **🔥 Aggressive**: Lower thresholds (45/25/15) = more signals, higher risk
- **🛡️ Conservative**: Higher thresholds (55/35/25) = fewer signals, lower risk  
- **💎 Quality Focus**: Minimum scores (B≥40, C≥25) = only best-in-tier signals

**Data Quality Features:**
- **🔍 Real Data Validation**: Extracts actual social links and metrics from APIs
- **🚫 Fake Data Detection**: Detects and flags fabricated transaction counts and holder growth
- **📊 Quality Scoring**: Each token receives a data quality score (0-100) for transparency

**Operational Settings:**
- **Scan Frequency**: 15-60 minutes (market dependent)
- **Signal Quality**: Minimum scores per tier prevent low-quality alerts
- **Price Targets**: Configurable per tier with separate stop losses

## 📁 Project Structure

```
meme-trading-bot/
├── src/
│   ├── analytics/          # Performance tracking
│   ├── discovery/          # Token discovery and validation
│   ├── notif/             # Telegram bot integration
│   ├── scoring/           # Signal scoring algorithms
│   ├── security/          # Security checks (honeypot detection)
│   ├── storage/           # Database operations
│   ├── config.py          # Configuration management
│   └── main.py            # Main bot logic
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── start_live_signals.py  # Live signal launcher
├── SIGNAL_FORMATS.md      # Signal format examples
└── TELEGRAM_SETUP_GUIDE.md # Setup instructions
```

## 🎯 What You'll Get

**See `SIGNAL_FORMATS.md` for complete signal examples.**

### Signal Channel Messages:
```
🚀 NEW MEME SIGNAL DETECTED!

🎯 Token: PEPECOIN (PEPE)
💰 Market Cap: $1.2M
📈 24h Change: +45.2%
💧 Liquidity: $250K
⚡ Volume: $500K

🔥 Signal Strength: STRONG
⚠️ Risk Level: MEDIUM

📍 Entry: $0.001234
🎯 Target 1: $0.002468 (+100%)
🎯 Target 2: $0.003702 (+200%)
🛑 Stop Loss: $0.000987 (-20%)

📋 Contract: So111111...
⏰ 2024-01-15 14:30:00 UTC
```

### Performance Channel Updates:
- Win/loss ratios
- Average gains per signal
- Best performing tokens
- Daily/weekly summaries

## 🛠️ Technical Details

- **Language**: Python 3.9+
- **APIs**: Birdeye, DexScreener
- **Database**: MySQL
- **Messaging**: Telegram Bot API
- **Scanning**: 30-minute intervals
- **Quality Threshold**: 80%+ confidence signals

## ⚙️ Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `SCAN_INTERVAL_MINUTES` | How often to scan for signals | 30 |
| `MIN_BOOM_SCORE` | Minimum signal score | 50 |
| `MIN_LIQUIDITY_USD` | Minimum liquidity required | $5,000 |
| `MAX_RISK_SCORE` | Maximum risk tolerance | 70 |

## 🔧 Troubleshooting

1. **Bot not sending messages**: Check Telegram bot permissions in channels
2. **No signals found**: Verify Birdeye API key and check market conditions
3. **Database errors**: Ensure MySQL is running and credentials are correct

## 📝 License

This project is for personal use only. Please ensure compliance with all relevant APIs' terms of service.

---

**⚠️ Disclaimer**: This bot is for educational and personal use only. Always do your own research before making any trading decisions. Cryptocurrency trading involves significant risk.
