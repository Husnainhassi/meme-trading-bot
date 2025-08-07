"""
Telegram bot module for sending trading signals and notifications.
"""

import requests
import sys
import os
from typing import Dict, List, Optional
import time
import asyncio

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import (
    TELEGRAM_BOT_TOKEN, SIGNAL_CHANNEL_ID, PERFORMANCE_CHANNEL_ID, CHAIN_ID,
    TIER_A_TARGET_1_PERCENT, TIER_A_TARGET_2_PERCENT, TIER_A_STOP_LOSS_PERCENT,
    TIER_B_TARGET_1_PERCENT, TIER_B_TARGET_2_PERCENT, TIER_B_STOP_LOSS_PERCENT,
    TIER_C_TARGET_1_PERCENT, TIER_C_TARGET_2_PERCENT, TIER_C_STOP_LOSS_PERCENT
)


class TelegramBot:
    """
    Handles sending trading signals and notifications via Telegram.
    """
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram bot.
        
        Args:
            bot_token: Telegram bot token from BotFather (optional, uses config)
            chat_id: Chat ID to send messages to (optional, uses config)
        """
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or SIGNAL_CHANNEL_ID  # Default to signal channel
        self.signal_channel_id = SIGNAL_CHANNEL_ID
        self.performance_channel_id = PERFORMANCE_CHANNEL_ID
        
        if not self.bot_token:
            print("⚠️ No Telegram bot token configured")
            return
            
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        # print(f"✅ Telegram bot initialized")
        # print(f"📱 Signal Channel: {self.signal_channel_id}")
        # print(f"📊 Performance Channel: {self.performance_channel_id}")
        
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to the configured chat.
        
        Args:
            message: Message text to send
            parse_mode: Message formatting (Markdown or HTML)
            
        Returns:
            Boolean indicating success
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            return True
            
        except requests.RequestException as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_alert(self, alert_type: str, message: str) -> bool:
        """
        Send a general alert message.
        
        Args:
            alert_type: Type of alert (INFO, WARNING, ERROR)
            message: Alert message
            
        Returns:
            Boolean indicating success
        """
        emoji = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '🚨'
        }.get(alert_type, '📢')
        
        formatted_message = f"{emoji} *{alert_type}*\n\n{message}"
        return self.send_message(formatted_message)
    
    def validate_connection(self) -> bool:
        """
        Validate if the bot token is valid and can communicate with Telegram API
        """
        if not self.bot_token:
            print("❌ No bot token provided")
            return False
            
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)  # Add 10 second timeout
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    # print(f"🤖 Bot Name: {bot_info.get('first_name', 'Unknown')}")
                    # print(f"🤖 Bot Username: @{bot_info.get('username', 'Unknown')}")
                    return True
            
            print(f"❌ Bot connection failed: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Bot connection error: {e}")
            return False

    async def send_to_channel(self, message: str, channel_id: str = None, parse_mode: str = None) -> bool:
        """
        Send message to a specific channel
        
        Args:
            message: Message text to send
            channel_id: Specific channel ID (uses default if None)
            parse_mode: Message formatting (Markdown or HTML)
            
        Returns:
            Boolean indicating success
        """
        target_channel = channel_id or self.chat_id
        
        if not target_channel:
            print("❌ No channel ID specified")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': target_channel,
                'text': message,
                'disable_web_page_preview': True
            }
            
            if parse_mode:
                payload['parse_mode'] = parse_mode
            
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    print(f"✅ Message sent to channel {target_channel}")
                    return True
                else:
                    print(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    async def send_performance_update(self, update_message: str) -> bool:
        """
        Send performance update to performance channel
        
        Args:
            update_message: Performance update text
            
        Returns:
            Boolean indicating success
        """
        return await self.send_to_channel(update_message, self.performance_channel_id)

    async def send_speculative_signal(self, token_address: str, comprehensive_result: Dict, pairs: List[Dict] = None) -> bool:
        """
        Send a speculative alert for tokens with strong momentum but not fully safe.
        Args:
            token_address: Token contract address
            comprehensive_result: Results from comprehensive evaluation
            pairs: Trading pairs data for additional metrics
        Returns:
            Boolean indicating success
        """
        try:
            tier = comprehensive_result.get('tier', 'D')
            score = comprehensive_result.get('comprehensive_score', 0)
            recommendation = comprehensive_result.get('recommendation', 'Speculative Opportunity')
            risk_level = comprehensive_result.get('risk_level', 'Unknown')
            strengths = comprehensive_result.get('strengths', [])[:3]
            red_flags = comprehensive_result.get('red_flags', [])[:2]
            market_cap = 0
            liquidity = 0
            volume_24h = 0
            price_change_24h = 0
            current_price = 0
            token_symbol = "UNKNOWN"
            if pairs:
                for pair in pairs:
                    if pair.get('fdv'):
                        market_cap = pair.get('fdv', 0)
                    liquidity_data = pair.get('liquidity', {})
                    if liquidity_data.get('usd'):
                        liquidity += liquidity_data.get('usd', 0)
                    if pair.get('volume', {}).get('h24'):
                        volume_24h = pair.get('volume', {}).get('h24', 0)
                    price_change = pair.get('priceChange', {})
                    if price_change.get('h24'):
                        price_change_24h = price_change.get('h24', 0)
                    if pair.get('priceUsd'):
                        current_price = float(pair.get('priceUsd', 0))
                    if pair.get('baseToken', {}).get('symbol'):
                        token_symbol = pair.get('baseToken', {}).get('symbol', "UNKNOWN")
                    break
            def format_market_cap(value):
                if value >= 1_000_000:
                    return f"${{value/1_000_000:.1f}}M"
                elif value >= 1_000:
                    return f"${{value/1_000:.1f}}K"
                else:
                    return f"${{value:.2f}}"
            def format_currency(value):
                if value >= 1_000_000:
                    return f"${{value/1_000_000:.1f}}M"
                elif value >= 1_000:
                    return f"${{value/1_000:.1f}}K"
                else:
                    return f"${{value:.2f}}"
            def format_price(price):
                if price < 0.000001:
                    return f"${{price:.8f}}"
                elif price < 0.001:
                    return f"${{price:.6f}}"
                elif price < 1:
                    return f"${{price:.4f}}"
                else:
                    return f"${{price:.2f}}"
            target_1_percent = TIER_C_TARGET_1_PERCENT
            target_2_percent = TIER_C_TARGET_2_PERCENT
            stop_loss_percent = TIER_C_STOP_LOSS_PERCENT
            target_1_price = current_price * (1 + target_1_percent / 100) if current_price > 0 else 0
            target_2_price = current_price * (1 + target_2_percent / 100) if current_price > 0 else 0
            stop_loss_price = current_price * (1 + stop_loss_percent / 100) if current_price > 0 else 0
            message = (
                f"⚠️ *SPECULATIVE MEME ALERT* ⚠️\n\n"
                f"🎯 Token: {token_symbol} ({token_symbol})\n"
                f"💰 Market Cap: {format_market_cap(market_cap)}\n"
                f"📈 24h Change: {'+' if price_change_24h >= 0 else ''}{price_change_24h:.1f}%\n"
                f"💧 Liquidity: {format_currency(liquidity)}\n"
                f"⚡️ Volume: {format_currency(volume_24h)}\n\n"
                f"🔎 *Speculative Opportunity*\n⚠️ Risk Level: {risk_level}\n\n"
                f"Entry: {format_price(current_price)}\n"
                f"🎯 Target 1: {format_price(target_1_price)} (+{target_1_percent}%)\n"
                f"🔵 Target 2: {format_price(target_2_price)} (+{target_2_percent}%)\n"
                f"🛑 Stop Loss: {format_price(stop_loss_price)} ({stop_loss_percent}%)\n\n"
                f"✅ Momentum Factors:\n{chr(10).join('• ' + s for s in strengths) if strengths else '• Some favorable metrics detected'}\n"
                f"⚠️ Safety Flags:\n{chr(10).join('• ' + f.replace('_', ' ').title() for f in red_flags) if red_flags else '• Standard meme coin risks apply'}\n\n"
                f"📋 Contract: `{token_address}`\n"
                f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                f"🔗 [DexScreener](https://dexscreener.com/solana/{token_address}) | [Birdeye](https://birdeye.so/token/{token_address})\n\n"
                f"*This is a speculative alert: High momentum, but not all safety checks passed. Trade with extra caution!*"
            )
            success = await self.send_to_channel(message, self.signal_channel_id)
            if success:
                print(f"⚠️ Speculative alert sent for {token_address[:8]}...")
            return success
        except Exception as e:
            print(f"❌ Error sending speculative signal: {e}")
            return False

    async def send_watchlist_notification(self, token_symbol: str, comprehensive_result: Dict) -> bool:
        """
        Send a notification for a token added to the watchlist.
        Args:
            token_symbol: Symbol of the token
            comprehensive_result: Results from comprehensive evaluation
        Returns:
            Boolean indicating success
        """
        try:
            score = comprehensive_result.get('comprehensive_score', 0)
            tier = comprehensive_result.get('tier', 'D')
            strengths = comprehensive_result.get('strengths', [])[:2]
            red_flags = comprehensive_result.get('red_flags', [])[:2]
            message = (
                f"👀 *Watchlist Candidate* 👀\n\n"
                f"Token: {token_symbol}\n"
                f"Score: {score:.1f}/100 (Tier {tier})\n\n"
                f"✅ Strengths:\n{chr(10).join('• ' + s for s in strengths) if strengths else '• Some positive factors'}\n"
                f"⚠️ Flags:\n{chr(10).join('• ' + f.replace('_', ' ').title() for f in red_flags) if red_flags else '• Standard risks'}\n\n"
                f"This token is close to meeting full criteria. Monitor for further developments!"
            )
            success = await self.send_to_channel(message, self.signal_channel_id)
            if success:
                print(f"👀 Watchlist notification sent for {token_symbol}")
            return success
        except Exception as e:
            print(f"❌ Error sending watchlist notification: {e}")
            return False
    # REMOVED: format_trading_signal() - Legacy formatting not used
    # Your bot only uses send_comprehensive_signal() for all signals

    async def send_comprehensive_signal(self, token_address: str, comprehensive_result: Dict, 
                                      risk_result: Dict, pairs: List[Dict] = None) -> bool:
        """
        Send a comprehensive trading signal with enhanced analysis.
        
        Args:
            token_address: Token contract address
            comprehensive_result: Results from comprehensive evaluation
            risk_result: Risk assessment results
            pairs: Trading pairs data for additional metrics
            
        Returns:
            Boolean indicating success
        """
        try:
            # Extract comprehensive analysis data
            tier = comprehensive_result.get('tier', 'D')
            score = comprehensive_result.get('comprehensive_score', 0)
            recommendation = comprehensive_result.get('recommendation', 'Unknown')
            risk_level = comprehensive_result.get('risk_level', 'Unknown')
            strengths = comprehensive_result.get('strengths', [])[:3]  # Top 3 strengths
            red_flags = comprehensive_result.get('red_flags', [])[:2]  # Top 2 concerns
            
            # Extract token metrics from pairs data
            market_cap = 0
            liquidity = 0
            volume_24h = 0
            price_change_24h = 0
            current_price = 0
            token_symbol = "UNKNOWN"
            
            if pairs:
                for pair in pairs:
                    # Get market cap
                    if pair.get('fdv'):
                        market_cap = pair.get('fdv', 0)
                    
                    # Get liquidity
                    liquidity_data = pair.get('liquidity', {})
                    if liquidity_data.get('usd'):
                        liquidity += liquidity_data.get('usd', 0)
                    
                    # Get volume
                    if pair.get('volume', {}).get('h24'):
                        volume_24h = pair.get('volume', {}).get('h24', 0)
                    
                    # Get price change
                    price_change = pair.get('priceChange', {})
                    if price_change.get('h24'):
                        price_change_24h = price_change.get('h24', 0)
                    
                    # Get current price
                    if pair.get('priceUsd'):
                        current_price = float(pair.get('priceUsd', 0))
                    
                    # Get token symbol
                    if pair.get('baseToken', {}).get('symbol'):
                        token_symbol = pair.get('baseToken', {}).get('symbol', "UNKNOWN")
                    
                    break  # Use first pair for main metrics
            
            # Format values
            def format_market_cap(value):
                if value >= 1_000_000:
                    return f"${value/1_000_000:.1f}M"
                elif value >= 1_000:
                    return f"${value/1_000:.1f}K"
                else:
                    return f"${value:.2f}"
            
            def format_currency(value):
                if value >= 1_000_000:
                    return f"${value/1_000_000:.1f}M"
                elif value >= 1_000:
                    return f"${value/1_000:.1f}K" 
                else:
                    return f"${value:.2f}"
            
            def format_price(price):
                if price < 0.000001:
                    return f"${price:.8f}"
                elif price < 0.001:
                    return f"${price:.6f}"
                elif price < 1:
                    return f"${price:.4f}"
                else:
                    return f"${price:.2f}"
            
            # Calculate price targets based on tier - REAL MEME COIN DYNAMICS
            target_1_percent = 50    # Default fallback for unknown tiers
            target_2_percent = 200
            stop_loss_percent = -60
            
            if tier == 'A':
                target_1_percent = TIER_A_TARGET_1_PERCENT     # Strong memes: +200%
                target_2_percent = TIER_A_TARGET_2_PERCENT     # Moon targets: +1000%
                stop_loss_percent = TIER_A_STOP_LOSS_PERCENT  # Volatile: -50%
            elif tier == 'B':
                target_1_percent = TIER_B_TARGET_1_PERCENT     # Good momentum: +100%
                target_2_percent = TIER_B_TARGET_2_PERCENT     # Strong pumps: +500%
                stop_loss_percent = TIER_B_STOP_LOSS_PERCENT  # Higher risk: -60%
            elif tier == 'C':
                target_1_percent = TIER_C_TARGET_1_PERCENT     # Quick gains: +50%
                target_2_percent = TIER_C_TARGET_2_PERCENT     # Decent pumps: +200%
                stop_loss_percent = TIER_C_STOP_LOSS_PERCENT  # Speculative: -70%
            
            # Calculate actual target prices
            target_1_price = current_price * (1 + target_1_percent / 100) if current_price > 0 else 0
            target_2_price = current_price * (1 + target_2_percent / 100) if current_price > 0 else 0
            stop_loss_price = current_price * (1 + stop_loss_percent / 100) if current_price > 0 else 0
            
            # Determine signal strength - MEME COIN APPROPRIATE MESSAGING
            if tier == 'A':
                signal_strength = "🚀 MOON POTENTIAL"  # High conviction for A-tier
            elif tier == 'B':
                signal_strength = "⚡ PUMP POTENTIAL"   # Good momentum signal
            else:
                signal_strength = "📈 EARLY SIGNAL"    # Speculative opportunity
            
            # Create meme-appropriate signal message with proper context
            message = f"""
🔥 MEME COIN PUMP ALERT 

🎯 Token: {token_symbol} ({token_symbol})
💰 Market Cap: {format_market_cap(market_cap)}
📈 24h Change: {'+' if price_change_24h >= 0 else ''}{price_change_24h:.1f}%
💧 Liquidity: {format_currency(liquidity)}
⚡️ Volume: {format_currency(volume_24h)}

� Analysis Level: {signal_strength}
⚠️ Risk Level: {risk_level}

� Entry: {format_price(current_price)}
🎯 Target 1: {format_price(target_1_price)} (+{target_1_percent}%)
🔵 Target 2: {format_price(target_2_price)} (+{target_2_percent}%)
🛑 Stop Loss: {format_price(stop_loss_price)} ({stop_loss_percent}%)

⚠️ MEME COIN TRADING WARNINGS:
• Extremely high risk - can lose 50-90% quickly
• Most meme coins go to zero
• Only risk what you can afford to lose completely
• Take profits quickly on any gains

📋 Contract: `{token_address}`
⏰ {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

📝 ANALYSIS SUMMARY:
• Tier: {tier} | Score: {score:.1f}/100
• Assessment: {recommendation}

✅ Positive Factors:
{chr(10).join(f'• {strength}' for strength in strengths[:3]) if strengths else '• Some favorable metrics detected'}

⚠️ Risk Factors:
{chr(10).join(f'• {flag.replace("_", " ").title()}' for flag in red_flags[:2]) if red_flags else '• Standard meme coin risks apply'}

🔗 Track & Trade:
[DexScreener](https://dexscreener.com/solana/{token_address})
[Birdeye](https://birdeye.so/token/{token_address})

⚡ Remember: In meme season, fortune favors the fast!
            """.strip()
            
            # Send to signal channel
            success = await self.send_to_channel(message, self.signal_channel_id)
            
            if success:
                print(f"📱 Comprehensive signal sent for {token_address[:8]}...")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending comprehensive signal: {e}")
            return False

def create_telegram_bot(bot_token: str, chat_id: str) -> Optional[TelegramBot]:
    """
    Create and test a Telegram bot instance.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID to send messages to
        
    Returns:
        TelegramBot instance if successful, None otherwise
    """
    if not bot_token or not chat_id:
        print("❌ Telegram bot token and chat ID are required")
        return None
    
    bot = TelegramBot(bot_token, chat_id)
    
    # print("🔗 Validating Telegram connection...")
    if bot.validate_connection():
        # print("✅ Telegram connection validated successfully")
        return bot
    else:
        print("⚠️ Telegram validation failed, but bot will continue")
        print("   (Network issues or API temporarily unavailable)")
        return bot  # Return bot anyway for offline functionality


def send_setup_test_message(bot_token: str, chat_id: str) -> bool:
    """
    Send a test message to verify Telegram setup.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID to send to
        
    Returns:
        Boolean indicating success
    """
    bot = create_telegram_bot(bot_token, chat_id)
    if bot:
        test_message = """
🤖 *Meme Trading Bot Test*

✅ Telegram integration is working!
🚀 Ready to send trading signals.

This is a test message from your meme trading bot.
"""
        return bot.send_message(test_message)
    
    return False

if __name__ == "__main__":
    print("📱 Testing Telegram Bot...")
    
    # For testing, you would need to set these environment variables
    # or pass them directly (not recommended for production)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if bot_token and chat_id:
        success = send_setup_test_message(bot_token, chat_id)
        print(f"Test message sent: {success}")
    else:
        print("❌ TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables required for testing")
        print("ℹ️ Add these to your .env file to test the Telegram integration")
