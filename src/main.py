"""
Main orchestration module for the meme trading bot.
Coordinates discovery, analysis, and notification process.
"""

import time
import sys
import os
import asyncio
from typing import Dict, List
from datetime import datetime

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.discovery.dexscreener import fetch_boosted_tokens, fetch_pairs
from src.security.honeypot_check import analyze_token_safety
from src.scoring.comprehensive_scorer import ComprehensiveTokenScorer
from src.discovery.enhanced_discovery import EnhancedTokenDiscovery
from src.storage.database import TokenDatabase
from src.notif.telegram_bot import create_telegram_bot
from src.config import (
    CHAIN_ID, SCAN_INTERVAL_MINUTES, MIN_BOOM_SCORE, MIN_LIQUIDITY_USD, MAX_RISK_SCORE,
    PAPER_TRADING, PAPER_STARTING_USD_BALANCE, PAPER_TRADE_AMOUNT_USD
)


class MemeBot:
    """
    Main bot orchestrator that coordinates all components.
    Adds paper trading mode for demo SOL trading.
    """
    
    def __init__(self, telegram_token: str = None, telegram_chat_id: str = None, paper_trading: bool = False, starting_usd: float = 10000.0):
        """
        Initialize the meme trading bot.
        
        Args:
            telegram_token: Telegram bot token (optional)
            telegram_chat_id: Telegram chat ID (optional)
            paper_trading: Enable paper trading mode
            starting_usd: Starting USD balance for paper trading
        """
        self.db = TokenDatabase()
        self.telegram_bot = None
        self.scorer = ComprehensiveTokenScorer()  # Initialize comprehensive scorer
        self.enhanced_discovery = EnhancedTokenDiscovery()  # Initialize enhanced discovery

        # Paper trading mode - USD based system
        self.paper_trading = paper_trading
        self.paper_usd_balance = starting_usd
        self.paper_trades = []  # List of dicts: {token_address, buy_price_usd, amount_usd, tokens_bought, time}

        # Initialize Telegram bot if credentials provided
        if telegram_token and telegram_chat_id:
            self.telegram_bot = create_telegram_bot(telegram_token, telegram_chat_id)
            if not self.telegram_bot:
                print("❌ Failed to initialize Telegram bot")
            else:
                # print("✅ Telegram bot initialized")
                pass

        # Scoring thresholds - configurable via environment variables
        self.min_boom_score = MIN_BOOM_SCORE        # Default: 50
        self.min_liquidity = MIN_LIQUIDITY_USD      # Default: 5000
        self.max_risk_score = MAX_RISK_SCORE        # Default: 70
        
        # print(f"🤖 Meme Bot initialized for {CHAIN_ID} chain")
        # print(f"⚙️ Thresholds: Boom≥{self.min_boom_score}, Liquidity≥${self.min_liquidity:,}, Risk≤{self.max_risk_score}")
        
    def get_config_summary(self) -> str:
        """Get a summary of current configuration"""
        from src.config import TIER_A_THRESHOLD, TIER_B_THRESHOLD, TIER_C_THRESHOLD
        return f"""
🔧 **Bot Configuration:**
• Chain: {CHAIN_ID}
• Scan Interval: {SCAN_INTERVAL_MINUTES} minutes
• Min Boom Score: {self.min_boom_score}
• Min Liquidity: ${self.min_liquidity:,}
• Max Risk Score: {self.max_risk_score}

📊 **Tier Thresholds:**
• Tier A (Strong Buy): ≥{TIER_A_THRESHOLD}/100
• Tier B (Monitor): ≥{TIER_B_THRESHOLD}/100  
• Tier C (Watch): ≥{TIER_C_THRESHOLD}/100
• Tier D (Avoid): <{TIER_C_THRESHOLD}/100
        """.strip()
    
    async def scan_and_analyze(self) -> List[Dict]:
        """
        Main scanning and analysis loop.
        
        Returns:
            List of analyzed tokens with signals
        """
        # print(f"\n🔍 Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            print("📡 Fetching boosted tokens...")
            boosted_tokens = []
            
            try:
                boosted_tokens = fetch_boosted_tokens()
            except Exception as api_err:
                print(f"❌ Error fetching boosted tokens: {api_err}")
                
            print(f"Found {len(boosted_tokens)} boosted tokens")
            if len(boosted_tokens) < 10:
                print(f"⚠️ Warning: Only {len(boosted_tokens)} tokens fetched. This may indicate an API issue, rate limit, or config problem.")
            if not boosted_tokens:
                print("❌ No tokens discovered. Check API keys, network, or API status.")
                return []

            analyzed_tokens = []
            signals_generated = 0
            errors_encountered = 0
            for i, token_address in enumerate(boosted_tokens, 1):
                print(f"\n🔬 Analyzing token {i}/{len(boosted_tokens)}: {token_address}")
                try:
                    pairs = []
                    try:
                        pairs = fetch_pairs(token_address)
                    except Exception as pair_err:
                        print(f"  ❌ Error fetching pairs: {pair_err}")
                        errors_encountered += 1
                        continue
                    if not pairs:
                        print("  ❌ No trading pairs found")
                        continue
                        
                    print("  🔒 Checking risks...")
                    try:
                        risk_result = analyze_token_safety(token_address, pairs)
                        print(f"  Risk Level: {risk_result['risk_level']}, Score: {risk_result['risk_score']}")
                    except Exception as risk_err:
                        print(f"  ❌ Error in risk assessment: {risk_err}")
                        errors_encountered += 1
                        continue
                    
                    print("  🎯 Running comprehensive evaluation...")
                    comprehensive_result = None
                    should_signal = False
                    try:
                        comprehensive_data = await self.enhanced_discovery.get_comprehensive_token_data(token_address, pairs)
                        comprehensive_result = await self.scorer.comprehensive_score(
                            comprehensive_data,
                            self._get_market_context()
                        )
                            
                        should_signal = self.scorer.should_send_signal_comprehensive(comprehensive_result.to_dict(), speculative_mode=True)
                        print(f"  📈 Comprehensive Score: {comprehensive_result.total_score:.1f}/100 (Tier {comprehensive_result.tier})")
                        if comprehensive_result.red_flags:
                            print(f"  🚩 Red Flags: {comprehensive_result.red_flags[0]}")
                        if comprehensive_result.strengths:
                            print(f"  💪 Strengths: {comprehensive_result.strengths[0]}")
                        print(f"  🎯 Signal Decision: {should_signal}")
                    except Exception as comp_err:
                        print(f"  ⚠️ Comprehensive evaluation failed: {comp_err}")
                        errors_encountered += 1
                        continue
                    
                    if should_signal and comprehensive_result:
                        signal_data = {
                            'token_address': token_address,
                            'risk_result': risk_result,
                            'pairs': pairs,
                            'total_liquidity': sum(p.get('liquidity', {}).get('usd', 0) or 0 for p in pairs),
                            'comprehensive_result': comprehensive_result.to_dict()
                        }
                        analyzed_tokens.append(signal_data)
                        signals_generated += 1
                        tier = comprehensive_result.tier
                        comp_score = comprehensive_result.total_score
                        print(f"  🎯 SIGNAL: Tier {tier} - {comp_score:.1f}/100")

                        # --- Paper Trading Logic ---
                        if self.paper_trading:
                            # Check if we already have this token in paper trades
                            existing_trade = self.db.get_paper_trade_by_address(token_address)
                            if existing_trade:
                                base_token = pairs[0].get('baseToken', {}) if pairs else {}
                                token_symbol = base_token.get('symbol', 'UNKNOWN')
                                print(f"  📝 [PAPER TRADE] Token {token_symbol} ({token_address[:8]}...) already exists in portfolio. Skipping.")
                            else:
                                # Find a pair with price data
                                selected_pair = None
                                for p in pairs:
                                    if p.get('priceUsd'):
                                        selected_pair = p
                                        break
                                if not selected_pair and pairs:
                                    selected_pair = pairs[0]  # fallback to first pair

                                if selected_pair:
                                    # Get price in USD (priceUSD), convert to float
                                    price_usd = selected_pair.get('priceUsd')
                                    try:
                                        buy_price_usd = float(price_usd) if price_usd else None
                                    except Exception:
                                        buy_price_usd = None
                                    
                                    # Get token symbol
                                    base_token = selected_pair.get('baseToken', {})
                                    token_symbol = base_token.get('symbol', 'UNKNOWN')
                                    
                                    # Use configured USD amount per trade (e.g., $25)
                                    trade_amount_usd = PAPER_TRADE_AMOUNT_USD
                                    
                                    # Check if we have enough balance
                                    if self.paper_usd_balance >= trade_amount_usd and buy_price_usd and buy_price_usd > 0:
                                        # Calculate how many tokens we can buy
                                        tokens_to_buy = trade_amount_usd / buy_price_usd
                                        
                                        # Deduct from USD balance
                                        # self.paper_usd_balance -= trade_amount_usd
                                        
                                        # Store paper trade in database
                                        self.db.store_paper_trade(
                                            token_address,
                                            token_symbol,
                                            buy_price_usd,
                                            trade_amount_usd,
                                            tokens_to_buy,
                                            datetime.now().isoformat()
                                        )
                                        
                                        # Add to local tracking
                                        self.paper_trades.append({
                                            'token_address': token_address,
                                            'token_symbol': token_symbol,
                                            'buy_price_usd': buy_price_usd,
                                            'amount_usd': trade_amount_usd,
                                            'tokens_bought': tokens_to_buy,
                                            'timestamp': datetime.now().isoformat()
                                        })
                                        
                                        print(f"  📝 [PAPER TRADE] Bought ${trade_amount_usd:.2f} of {token_symbol} ({token_address[:8]}...) at ${buy_price_usd:.8f}/token ({tokens_to_buy:.2f} tokens). Remaining balance: ${self.paper_usd_balance:.2f}")
                                    elif self.paper_usd_balance < trade_amount_usd:
                                        print(f"  ⚠️ [PAPER TRADE] Not enough balance to buy {token_symbol}. Need ${trade_amount_usd:.2f}, have ${self.paper_usd_balance:.2f}")
                                    else:
                                        print(f"  ⚠️ [PAPER TRADE] Could not determine USD price for {token_symbol} ({token_address[:8]}...)")
                                else:
                                    print(f"  ⚠️ [PAPER TRADE] No valid pair found for {token_address[:8]}...")
                        # --- End Updated Paper Trading Logic ---
                        
                        if self.telegram_bot:
                            try:
                                await self._send_trading_signal(signal_data)
                            except Exception as tg_err:
                                print(f"  ⚠️ Error sending Telegram signal: {tg_err}")
                    else:
                        # --- Speculative Alert Logic ---
                        if comprehensive_result and self.scorer.is_speculative_candidate(comprehensive_result):
                            print(f"  ⚡ Speculative candidate detected: {comprehensive_result.total_score:.1f}/100")
                            if self.telegram_bot:
                                try:
                                    await self.telegram_bot.send_speculative_signal(
                                        token_address,
                                        comprehensive_result.to_dict(),
                                        pairs
                                    )
                                except Exception as tg_err:
                                    print(f"  ⚠️ Error sending speculative Telegram alert: {tg_err}")
                        # --- Watchlist Logic ---
                        if comprehensive_result and self.scorer.is_watchlist_candidate(comprehensive_result):
                            print(f"  👀 Watchlist candidate: {comprehensive_result.total_score:.1f}/100")
                            self.scorer.add_to_watchlist(token_address, comprehensive_result)
                            if self.telegram_bot:
                                try:
                                    await self.telegram_bot.send_watchlist_notification(
                                        token_address,
                                        comprehensive_result.to_dict()
                                    )
                                except Exception as tg_err:
                                    print(f"  ⚠️ Error sending watchlist Telegram alert: {tg_err}")
                        if comprehensive_result:
                            comp_score = comprehensive_result.total_score
                            tier = comprehensive_result.tier
                            print(f"  ⏭️ Skipped: Tier {tier} ({comp_score:.1f}/100) - Below threshold")
                        else:
                            print(f"  ⏭️ Skipped: Comprehensive analysis failed or high risk")

                    time.sleep(1)

                except Exception as e:
                    print(f"  ❌ Error analyzing token: {e}")
                    errors_encountered += 1
                    continue
            
            print(f"\n✅ Scan completed: {signals_generated} signals generated from {len(boosted_tokens)} tokens")
            if self.paper_trading:
                print("\n==== PAPER TRADING SUMMARY ====")
                print(f"USD Balance: ${self.paper_usd_balance:.2f}")
                total_invested = len(self.paper_trades) * PAPER_TRADE_AMOUNT_USD
                print(f"Total Invested: ${total_invested:.2f}")
                if self.paper_trades:
                    print("Recent Trades:")
                    for t in self.paper_trades[-3:]:  # Show last 3 trades
                        print(f"  • {t['token_symbol']}: ${t['amount_usd']:.2f} at ${t['buy_price_usd']:.8f}/token ({t['tokens_bought']:.2f} tokens)")
                else:
                    print("No paper trades executed this scan.")
                print("==============================\n")
            if errors_encountered > 0:
                print(f"⚠️ {errors_encountered} errors encountered during scan. Check logs above for details.")
            if signals_generated == 0 and len(boosted_tokens) > 0:
                print(f"⚠️ No signals generated. All tokens may have failed scoring, been filtered, or encountered errors.")
            return analyzed_tokens
        except Exception as e:
            print(f"❌ Error during scan: {e}")
            return []
    
    async def _send_trading_signal(self, signal_data: Dict) -> bool:
        """
        Send a trading signal via Telegram.
        
        Args:
            signal_data: Signal data including token and analysis results
            
        Returns:
            Boolean indicating success
        """
        try:
            token_address = signal_data['token_address']
            risk_result = signal_data['risk_result']
            comprehensive_result = signal_data.get('comprehensive_result')
            
            # Store signal in database with comprehensive score
            signal_type = 'BUY' if comprehensive_result and comprehensive_result.get('tier') in ['A', 'B'] else 'MONITOR'
            signal_score = comprehensive_result.get('comprehensive_score', 0) if comprehensive_result else 0


            # Extract current price using the same logic as send_comprehensive_signal (first priceUsd from pairs)
            pairs = signal_data.get('pairs', [])
            current_price = None
            if pairs:
                for pair in pairs:
                    if pair.get('priceUsd'):
                        try:
                            current_price = float(pair.get('priceUsd', 0))
                        except Exception:
                            current_price = None
                        break



            # Entry target = current price
            entry_target = current_price

            # Take profits and stop loss as simple multiples
            tp_sl_positions = self.scorer.get_tp_sl_position(current_price, comprehensive_result)

            # Store signal in database (update your store_signal to accept these fields)
            
            targets = {
                'current_price': current_price,
                'entry_target': entry_target,
                'take_profit_1': tp_sl_positions.get('target_1_percent'),
                'take_profit_2': tp_sl_positions.get('target_2_percent'),
                'target_1_price': tp_sl_positions.get('target_1_price'),
                'target_2_price': tp_sl_positions.get('target_2_price'),
                'stop_loss_price': tp_sl_positions.get('stop_loss_price'),
                'stop_loss': tp_sl_positions.get('stop_loss_percent')
            }
            self.db.store_signal(
                token_address, 
                signal_type, 
                signal_score,
                risk_result['risk_level'],
                targets
            )

            # Send Telegram message using comprehensive signal format
            success = await self.telegram_bot.send_comprehensive_signal(
                token_address,
                comprehensive_result or {},  # Pass empty dict if None
                risk_result,
                pairs  # Pass pairs data for market metrics
            )

            if success:
                print("  📱 Telegram signal sent")
            else:
                print("  ❌ Failed to send Telegram signal")

            return success

        except Exception as e:
            print(f"❌ Error sending signal: {e}")
            return False
    
    async def run_continuous_async(self, scan_interval_minutes: int = 30):
        """
        Run the bot continuously with async support.
        
        Args:
            scan_interval_minutes: Minutes between scans
        """
        # print(f"🔄 Starting continuous mode (scanning every {scan_interval_minutes} minutes)")
        
        if self.telegram_bot:
            self.telegram_bot.send_alert("INFO", f"🚀 Meme Bot started (scan interval: {scan_interval_minutes}m)")
        
        try:
            while True:
                try:
                    # Run scan and analysis
                    
                    await self.scan_and_analyze()
                    
                    # Wait for next scan
                    print(f"⏰ Next scan in {SCAN_INTERVAL_MINUTES} minutes...")
                    await asyncio.sleep(SCAN_INTERVAL_MINUTES * 60)
                    
                except Exception as e:
                    print(f"❌ Error in scan cycle: {e}")
                    if self.telegram_bot:
                        self.telegram_bot.send_alert("ERROR", f"⚠️ Scan error: {str(e)}")
                    
                    # Wait a shorter time on error
                    await asyncio.sleep(300)  # 5 minutes
                
        except KeyboardInterrupt:
            print("\n⏹️ Bot stopped by user")
            if self.telegram_bot:
                self.telegram_bot.send_alert("INFO", "🛑 Meme Bot stopped")
        except Exception as e:
            print(f"\n❌ Bot crashed: {e}")
            if self.telegram_bot:
                self.telegram_bot.send_alert("ERROR", f"🚨 Bot crashed: {str(e)}")


    def _get_market_context(self) -> Dict:
        """Get current market context for comprehensive evaluation"""
        # This could be enhanced to fetch real market data
        # For now, return a basic context
        return {
            'crypto_sentiment': 'neutral',  # Could fetch from sentiment APIs
            'meme_cycle_position': 'mid',   # Could analyze based on recent meme coin performance
            'positive_catalysts': False,    # Could check news/events
            'condition': 'sideways'         # bull_market, bear_market, sideways
        }
    

def main():
    """Main entry point."""
    print("🤖 Meme Trading Bot v1.0")
    print("=" * 40)

    # Load configuration from environment
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    scan_interval = int(os.getenv("SCAN_INTERVAL_MINUTES", "30"))

    # Paper trading mode config - use config values
    paper_trading = PAPER_TRADING
    starting_usd = PAPER_STARTING_USD_BALANCE
    trade_amount = PAPER_TRADE_AMOUNT_USD
    
    # print(f"Paper trading mode: {'Enabled' if paper_trading else 'Disabled'}")
    # if paper_trading:
    #     print(f"Starting balance: ${starting_usd:,.2f}")
    #     print(f"Trade amount: ${trade_amount:.2f} per trade")

    # Initialize bot
    bot = MemeBot(telegram_token, telegram_chat_id, paper_trading=paper_trading, starting_usd=starting_usd)

    # Choose mode
    mode = os.getenv("BOT_MODE", "single").lower()

    if mode == "continuous":
        asyncio.run(bot.run_continuous_async(scan_interval))
    else:
        # Single scan mode
        print("🔍 Running single scan...")
        signals = asyncio.run(bot.scan_and_analyze())

        if signals:
            print(f"\n📈 {len(signals)} signals generated:")
            for signal in signals:
                comp = signal.get('comprehensive_result')
                if comp:
                    tier = comp.get('tier', 'D')
                    score = comp.get('comprehensive_score', 0)
                    print(f"  • {signal['token_address'][:20]}... - Tier {tier} ({score:.1f}/100)")
                else:
                    print(f"  • {signal['token_address'][:20]}... - No comprehensive analysis")
        else:
            print("\n📊 No signals generated this scan")


if __name__ == "__main__":
    main()
