"""
Cron job class for monitoring open paper trades, updating their performance, and sending results to the performance channel.
"""

import sys
import os
from datetime import datetime
from typing import List, Dict


# Add the project root to the Python path so 'src' is importable
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.storage.database import TokenDatabase
from src.notif.telegram_bot import create_telegram_bot
from src.discovery.dexscreener import fetch_pairs

class PaperTradePerformanceCron:
    def __init__(self, telegram_token: str, performance_channel_id: str):
        self.db = TokenDatabase()
        self.telegram_bot = create_telegram_bot(telegram_token, performance_channel_id)

    def fetch_and_update_trades(self) -> List[Dict]:
        open_trades = self.db.get_open_paper_trades()
        self.total_pnl_usd = 0
        self.profitable = 0
        self.losses = 0
        trade_rows = []
        seen = set()

        for trade in open_trades:
            token_address = trade['token_address']
            token_symbol = trade.get('token_symbol', 'UNKNOWN')
            buy_price_usd = float(trade.get('buy_price_usd', 0))  # USD price at buy
            amount_usd = float(trade.get('amount_usd', 0))  # USD amount spent
            tokens_bought = float(trade.get('tokens_bought', 0))  # Number of tokens bought
            trade_id = trade['id']
            buy_timestamp = trade.get('buy_timestamp')
            
            # Skip zero price trades or missing data
            if buy_price_usd == 0 or amount_usd == 0 or tokens_bought == 0:
                continue
                
            # Group by token+address (show only latest trade per token+address)
            key = (token_symbol, token_address)
            if key in seen:
                continue
            seen.add(key)
            
            # Fetch latest price from DEXScreener
            pairs = []
            try:
                pairs = fetch_pairs(token_address)
            except Exception as e:
                print(f"Error fetching pairs for {token_address[:8]}...: {e}")
                continue
                
            # Get current price in USD
            latest_price_usd = None
            if pairs:
                # Try to find any pair with USD price
                for p in pairs:
                    if p.get('priceUsd'):
                        try:
                            latest_price_usd = float(p.get('priceUsd', 0))
                            break
                        except Exception:
                            continue
                        
            if latest_price_usd is None or latest_price_usd == 0:
                print(f"Could not fetch latest USD price for {token_address[:8]}...")
                continue
                
            # Calculate current value: tokens_bought * latest_price_usd
            current_value_usd = tokens_bought * latest_price_usd
            
            # P/L in USD: current_value - amount_spent
            pnl_usd = current_value_usd - amount_usd
            
            # P/L percentage: based on USD price change
            pnl_pct = ((latest_price_usd - buy_price_usd) / buy_price_usd * 100) if buy_price_usd > 0 else 0
            
            # Update totals
            self.total_pnl_usd += pnl_usd
            if pnl_usd >= 0:
                self.profitable += 1
            else:
                self.losses += 1
                
            # Update trade in DB with latest price and P/L in USD
            self.db.update_paper_trade_performance(trade_id, latest_price_usd, pnl_usd)
            
            # Add to table rows
            trade_rows.append({
                'token_symbol': token_symbol,
                'token_address': token_address,
                'buy_price': buy_price_usd,
                'latest_price': latest_price_usd,
                'amount_usd': amount_usd,
                'tokens_bought': tokens_bought,
                'pnl_usd': pnl_usd,
                'pnl_pct': pnl_pct,
                'buy_timestamp': buy_timestamp,
                'current_value_usd': current_value_usd
            })
        return trade_rows

    def build_report(self, trade_rows: List[Dict]) -> str:
        # Sort trades by P/L percentage (best performers first)
        sorted_trades = sorted(trade_rows, key=lambda x: x['pnl_pct'], reverse=True)
        
        # Build individual trade cards with better formatting
        trade_cards = []
        for i, row in enumerate(sorted_trades, 1):
            # Determine emoji based on performance
            if row['pnl_pct'] >= 50:
                status_emoji = "🚀"
            elif row['pnl_pct'] >= 10:
                status_emoji = "📈"
            elif row['pnl_pct'] >= 0:
                status_emoji = "🟢"
            elif row['pnl_pct'] >= -10:
                status_emoji = "🟡"
            else:
                status_emoji = "🔴"
            
            # Format P/L with better readability
            pnl_sign = "+" if row['pnl_usd'] >= 0 else ""
            pnl_pct_sign = "+" if row['pnl_pct'] >= 0 else ""
            
            # Shorten token address for better display
            short_address = f"{row['token_address'][:6]}...{row['token_address'][-4:]}"
            long_address = f"{row['token_address']}"
            
            trade_card = f"""
{status_emoji} {row['token_symbol']} #{i}
`{long_address}`

💰 Investment: ${row['amount_usd']:.2f}
📊 Price: ${row['buy_price']:.8f} → ${row['latest_price']:.8f}
🪙 Tokens: {row['tokens_bought']:,.0f}

💵 P/L: {pnl_sign}${row['pnl_usd']:.2f} ({pnl_pct_sign}{row['pnl_pct']:.1f}%)
📅 Date: {str(row['buy_timestamp'])[:16]}
"""
            trade_cards.append(trade_card)
        
        # Calculate summary statistics
        total_invested = sum(row['amount_usd'] for row in trade_rows)
        total_current_value = total_invested + self.total_pnl_usd
        overall_pct = (self.total_pnl_usd / total_invested * 100) if total_invested > 0 else 0
        win_rate = (self.profitable / len(trade_rows) * 100) if trade_rows else 0
        
        # Build summary with better formatting
        summary_emoji = "🚀" if overall_pct >= 10 else "📈" if overall_pct >= 0 else "📉"
        pnl_sign = "+" if self.total_pnl_usd >= 0 else ""
        overall_sign = "+" if overall_pct >= 0 else ""
        
        from datetime import timezone
        checked_time = datetime.now(timezone.utc).strftime('%H:%M UTC')
        
        # Combine everything into a beautiful report
        trades_section = "─" * 35 + "\n" + "\n".join(trade_cards)
        
        report = f"""
📊 PAPER TRADING PORTFOLIO
🕐 Updated: {checked_time}*

{trades_section}

{summary_emoji} PORTFOLIO SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💼 Total Invested: ${total_invested:.2f}
💵 Current Value: ${total_current_value:.2f}
📊 Total P/L: {pnl_sign}${self.total_pnl_usd:.2f} ({overall_sign}{overall_pct:.1f}%)

🎯 Performance Stats:
✅ Winners: {self.profitable} trades
❌ Losers: {self.losses} trades  
🏆 Win Rate: {win_rate:.1f}%

💡 *Sorted by performance (best first)*
🚀 +50%+ | 📈 +10%+ | 🟢 Profit | 🟡 -10% | 🔴 -10%+
"""
        return report

    def send_report(self, report: str):
        if self.telegram_bot:
            import asyncio
            asyncio.run(self.telegram_bot.send_performance_update(report))
        else:
            print("Telegram bot not initialized. Report not sent.")

if __name__ == "__main__":
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    PERFORMANCE_CHANNEL_ID = os.getenv("PERFORMANCE_CHANNEL_ID")
    cron = PaperTradePerformanceCron(TELEGRAM_BOT_TOKEN, PERFORMANCE_CHANNEL_ID)
    summary_lines = cron.fetch_and_update_trades()
    if summary_lines:
        report = cron.build_report(summary_lines)
        cron.send_report(report)
        print("Performance report sent.")
    else:
        print("No open paper trades to monitor.")
