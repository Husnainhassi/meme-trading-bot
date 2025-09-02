"""
Enhanced Token Scorer implementing comprehensive meme coin evaluation framework
Research-backed multi-dimensional analysis for identifying 5x+ potential
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
import os
import sys

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import (
    TIER_A_THRESHOLD, TIER_B_THRESHOLD, TIER_C_THRESHOLD,
    TIER_A_ALWAYS_SIGNAL, TIER_B_MIN_SCORE, TIER_C_MIN_SCORE, TIER_D_NEVER_SIGNAL,
    TIER_A_TARGET_1_PERCENT, TIER_A_TARGET_2_PERCENT, TIER_A_STOP_LOSS_PERCENT,
    TIER_B_TARGET_1_PERCENT, TIER_B_TARGET_2_PERCENT, TIER_B_STOP_LOSS_PERCENT,
    TIER_C_TARGET_1_PERCENT, TIER_C_TARGET_2_PERCENT, TIER_C_STOP_LOSS_PERCENT
)

@dataclass
class ScoringResult:
    """Container for comprehensive scoring results"""
    total_score: float = 0.0
    tier: str = 'D'
    category_scores: Dict[str, float] = field(default_factory=dict)
    red_flags: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendation: str = 'AVOID'
    risk_level: str = 'HIGH'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for compatibility"""
        return {
            'comprehensive_score': self.total_score,
            'tier': self.tier,
            'category_scores': self.category_scores,
            'red_flags': self.red_flags,
            'strengths': self.strengths,
            'recommendation': self.recommendation,
            'risk_level': self.risk_level
        }
    
class ComprehensiveTokenScorer:
    # --- Speculative and Watchlist Features ---
    def is_speculative_candidate(self, result: Any) -> bool:
        """
        Determine if a token should trigger a speculative alert:
        - Strong momentum (market_dynamics or community_signals high)
        - Not a critical red flag (e.g., not honeypot, not extreme sell tax)
        - Fails some safety checks (e.g., not Tier A/B, but high in momentum)
        Accepts both ScoringResult and dict.
        If 'tier' is missing, log a warning and return False.
        """
        if not result:
            return False
        # Handle both ScoringResult object and dict
        tier = None
        market = 0
        social = 0
        risk_level = 'HIGH'
        total_score = 0
        if hasattr(result, 'tier'):
            tier = getattr(result, 'tier', None)
            market = getattr(result, 'category_scores', {}).get('market_dynamics', 0)
            social = getattr(result, 'category_scores', {}).get('community_signals', 0)
            risk_level = getattr(result, 'risk_level', 'HIGH')
            total_score = getattr(result, 'total_score', 0)
        elif isinstance(result, dict):
            tier = result.get('tier')
            category_scores = result.get('category_scores', {})
            market = category_scores.get('market_dynamics', 0)
            social = category_scores.get('community_signals', 0)
            risk_level = result.get('risk_level', 'HIGH')
            total_score = result.get('comprehensive_score', 0)
        if tier is None:
            self.logger.warning("is_speculative_candidate: 'tier' missing in result, cannot evaluate speculative status.")
            return False
        if tier in ('A', 'B'):
            return False
        if risk_level == 'CRITICAL':
            return False
        if (market >= 12 or social >= 12) and total_score >= 18:
            return True
        return False

    def is_watchlist_candidate(self, result: Any) -> bool:
        """
        Determine if a token should be added to the watchlist:
        - Score is within 5 points of Tier C threshold
        - Not already Tier A/B/C
        Accepts both ScoringResult and dict.
        """
        if not result:
            return False
        if hasattr(result, 'tier'):
            tier = result.tier
            total_score = result.total_score
        else:
            tier = result.get('tier', 'D')
            total_score = result.get('comprehensive_score', 0)
        if tier in ('A', 'B', 'C'):
            return False
        tier_c = self.TIER_THRESHOLDS['C']
        if tier_c - 5 <= total_score < tier_c:
            return True
        return False

    def add_to_watchlist(self, token_symbol: str, result: ScoringResult, watchlist_path: str = "watchlist.txt"):
        """Append token to a simple watchlist file."""
        try:
            with open(watchlist_path, "a") as f:
                f.write(f"{token_symbol}: Score {result.total_score:.1f}, Tier {result.tier}, Flags: {','.join(result.red_flags)}\n")
        except Exception as e:
            self.logger.error(f"Failed to add to watchlist: {e}")

    def load_watchlist(self, watchlist_path: str = "watchlist.txt") -> list:
        """Load the current watchlist."""
        try:
            with open(watchlist_path, "r") as f:
                return f.readlines()
        except Exception:
            return []
    """
    Advanced token scoring system based on research-backed evaluation framework
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Scoring thresholds - configurable via environment variables
        self.TIER_THRESHOLDS = {
            'A': TIER_A_THRESHOLD,  # Default: 50 - Strong Buy
            'B': TIER_B_THRESHOLD,  # Default: 30 - Monitor/Small Position  
            'C': TIER_C_THRESHOLD,  # Default: 20 - Watch List
            'D': 0                  # Avoid
        }
        
        # Signal generation criteria - configurable
        self.SIGNAL_CRITERIA = {
            'tier_a_always': TIER_A_ALWAYS_SIGNAL,     # Default: True
            'tier_b_min_score': TIER_B_MIN_SCORE,      # Default: 40
            'tier_c_min_score': TIER_C_MIN_SCORE,      # Default: 25
            'tier_d_never': TIER_D_NEVER_SIGNAL        # Default: True
        }
        
        # Critical red flags that auto-disqualify - MEME-FOCUSED SAFETY
        self.CRITICAL_RED_FLAGS = [
            'CRITICAL_HONEYPOT',        # Absolute dealbreaker - can't sell
            'extreme_sell_tax',         # >30% sell tax = can't exit
            'insufficient_liquidity',   # Can't actually trade
            'whale_dumping',           # Large wallets dumping
            'sentiment_crash',         # Social sentiment collapsing
            'safety_analysis_error'    # Couldn't verify safety
        ]
        
        # Weight multipliers for different market conditions
        self.MARKET_CONDITION_WEIGHTS = {
            'bull_market': {'community': 1.2, 'timing': 1.3, 'technical': 0.9},
            'bear_market': {'security': 1.3, 'technical': 1.2, 'timing': 0.8},
            'sideways': {'security': 1.1, 'community': 1.1, 'market': 1.0}
        }
    
    async def comprehensive_score(self, token_data: Dict[str, Any], 
                                market_context: Optional[Dict] = None) -> ScoringResult:
        """
        Main scoring function implementing the comprehensive evaluation framework
        """
        try:
            # Initialize scoring categories
            scores = {
                'on_chain_health': 0,
                'market_dynamics': 0, 
                'community_signals': 0,
                'technical_foundation': 0,
                'timing_factors': 0,
                'risk_deductions': 0
            }
            
            red_flags = []
            strengths = []
            
            # 1. On-Chain Health & Security (25 points)
            scores['on_chain_health'], health_flags, health_strengths = await self._score_onchain_health(token_data)
            red_flags.extend(health_flags)
            strengths.extend(health_strengths)
            
            # 2. Market Dynamics & Trading Metrics (20 points)
            scores['market_dynamics'], market_flags, market_strengths = await self._score_market_dynamics(token_data)
            red_flags.extend(market_flags)
            strengths.extend(market_strengths)
            
            # 3. Community & Social Signals (20 points)
            scores['community_signals'], community_flags, community_strengths = await self._score_community_signals(token_data)
            red_flags.extend(community_flags)
            strengths.extend(community_strengths)
            
            # 4. Technical & Development (15 points)
            scores['technical_foundation'], tech_flags, tech_strengths = await self._score_technical_foundation(token_data)
            red_flags.extend(tech_flags)
            strengths.extend(tech_strengths)
            
            # 5. Timing & Market Context (10 points)
            scores['timing_factors'], timing_flags, timing_strengths = await self._score_timing_factors(token_data, market_context)
            red_flags.extend(timing_flags)
            strengths.extend(timing_strengths)
            
            # 6. Risk Factors & Red Flags (deductions)
            scores['risk_deductions'], risk_flags = await self._score_risk_factors(token_data, red_flags)
            red_flags.extend(risk_flags)
            
            # Check for critical red flags (auto-disqualify)
            critical_flags = [flag for flag in red_flags if flag in self.CRITICAL_RED_FLAGS]
            if critical_flags:
                return ScoringResult(
                    total_score=0,
                    tier='D',
                    category_scores=scores,
                    red_flags=red_flags,
                    strengths=strengths,
                    recommendation="AVOID - Critical red flags detected",
                    risk_level="CRITICAL"
                )
            
            # Calculate total score
            total_score = sum(scores.values()) - scores['risk_deductions']
            total_score = max(0, min(100, total_score))  # Clamp between 0-100
            
            # Apply market condition adjustments if provided
            if market_context:
                total_score = self._apply_market_adjustments(total_score, scores, market_context)
            
            # Determine tier and recommendation
            tier = self._determine_tier(total_score)
            recommendation = self._generate_recommendation(tier, total_score, red_flags, strengths)
            risk_level = self._assess_risk_level(total_score, red_flags)
            
            return ScoringResult(
                total_score=total_score,
                tier=tier,
                category_scores=scores,
                red_flags=red_flags,
                strengths=strengths,
                recommendation=recommendation,
                risk_level=risk_level
            )
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive scoring: {e}")
            return ScoringResult(
                total_score=0,
                tier='D',
                category_scores={},
                red_flags=['scoring_error'],
                strengths=[],
                recommendation="AVOID - Scoring error",
                risk_level="CRITICAL"
            )
    
    async def _score_onchain_health(self, token_data: Dict) -> Tuple[float, List[str], List[str]]:
        """Score IMMEDIATE security and trading safety (25 points) - MEME-OPTIMIZED"""
        score = 0
        flags = []
        strengths = []
        print("\n[On-Chain Health & Security Scoring]")
        
        try:
            # ⚡ IMMEDIATE SAFETY CHECKS (15 points) - CRITICAL FOR MEME TRADING
            
            # Honeypot detection - ABSOLUTE PRIORITY
            honeypot_status = token_data.get('honeypot_check', {})
            is_honeypot = honeypot_status.get('is_honeypot', True)
            can_sell = honeypot_status.get('can_sell', False)
            
            if not is_honeypot and can_sell:
                score += 8  # Maximum points for trading safety
                print("Honeypot check: +8 (SAFE TO TRADE)")
                strengths.append("✅ SAFE TO TRADE - Not a honeypot")
            elif can_sell:
                score += 5
                print("Honeypot check: +5 (Can sell but check carefully)")
                strengths.append("⚠️ Can sell but check carefully")
            else:
                print("Honeypot check: 0 (CRITICAL_HONEYPOT)")
                flags.append("CRITICAL_HONEYPOT")  # Critical flag
                return score, flags, strengths  # Don't continue if honeypot
            
            # Buy/sell tax analysis - practical trading concern
            buy_tax = token_data.get('buy_tax_percentage', 0)
            sell_tax = token_data.get('sell_tax_percentage', 0)
            
            if buy_tax <= 5 and sell_tax <= 10:  # Reasonable taxes
                score += 4
                print(f"Buy/Sell tax: +4 (Low taxes: Buy {buy_tax}%, Sell {sell_tax}%)")
                strengths.append(f"💰 Low taxes - Buy: {buy_tax}%, Sell: {sell_tax}%")
            elif buy_tax <= 10 and sell_tax <= 20:  # Acceptable
                score += 2
                print(f"Buy/Sell tax: +2 (Moderate taxes: Buy {buy_tax}%, Sell {sell_tax}%)")
                strengths.append("📊 Moderate taxes")
            elif sell_tax > 30:  # Too high to trade
                print(f"Buy/Sell tax: 0 (Extreme sell tax: {sell_tax}%)")
                flags.append("extreme_sell_tax")
            
            # Trading restrictions
            max_tx_amount = token_data.get('max_transaction_percentage', 100)
            if max_tx_amount >= 1:  # At least 1% of supply per transaction
                score += 2
                print("Transaction limits: +2 (No restrictive limits)")
                strengths.append("🔄 No restrictive transaction limits")
            elif max_tx_amount < 0.1:
                print("Transaction limits: 0 (Restrictive limits)")
                flags.append("restrictive_tx_limits")
            
            # Contract pause/emergency functions
            has_pause_function = token_data.get('has_pause_function', False)
            if not has_pause_function:
                score += 1
                print("Pause function: +1 (No pause function)")
                strengths.append("🔒 No pause function")
            else:
                print("Pause function: 0 (Has pause function)")
                flags.append("has_pause_risk")
            
            # 💧 LIQUIDITY SAFETY (5 points) - CAN WE ACTUALLY TRADE?
            
            liquidity_info = token_data.get('liquidity', {})
            pool_size = liquidity_info.get('usd', 0)
            is_locked = liquidity_info.get('locked', False)
            
            # Minimum liquidity for safe trading
            if pool_size >= 20000:  # $20k minimum for decent trades
                score += 3
                print(f"Liquidity pool: +3 (Sufficient: ${pool_size:,.0f})")
                strengths.append("💧 Sufficient liquidity for trading")
            elif pool_size >= 5000:  # $5k bare minimum
                score += 2
                print(f"Liquidity pool: +2 (Basic: ${pool_size:,.0f})")
                strengths.append("🌊 Basic liquidity available")
            elif pool_size >= 1000:  # Very low but tradeable
                score += 1
                print(f"Liquidity pool: +1 (Minimal: ${pool_size:,.0f})")
                strengths.append("💦 Minimal liquidity")
            else:
                print(f"Liquidity pool: 0 (Insufficient: ${pool_size:,.0f})")
                flags.append("insufficient_liquidity")
            
            # LP lock status - protection against rug pulls
            if is_locked:
                score += 2
                print("Liquidity lock: +2 (Locked)")
                strengths.append("🔐 Liquidity locked - Rug protection")
            else:
                print("Liquidity lock: 0 (Unlocked)")
                flags.append("unlocked_liquidity")
            
            # 🔍 CONTRACT BASICS (5 points) - MINIMAL SECURITY CHECKS
            
            contract_info = token_data.get('contract', {})
            
            # Ownership status - decentralization indicator
            ownership = contract_info.get('ownership', 'unknown')
            if ownership == 'renounced':
                score += 3
                print("Ownership: +3 (Renounced)")
                strengths.append("👤 Ownership renounced - Decentralized")
            elif ownership == 'multisig':
                score += 1
                print("Ownership: +1 (Multisig)")
                strengths.append("🤝 Multi-signature ownership")
            else:
                print("Ownership: 0 (Centralized)")
                flags.append("centralized_control")
            
            # Mint function disabled
            can_mint = contract_info.get('can_mint', True)
            if not can_mint:
                score += 2
                print("Mint function: +2 (No mint function)")
                strengths.append("🚫 No mint function - Fixed supply")
            else:
                print("Mint function: 0 (Unlimited minting)")
                flags.append("unlimited_minting")
            
        except Exception as e:
            self.logger.error(f"Error scoring immediate safety: {e}")
            flags.append("safety_analysis_error")
        
        return score, flags, strengths
    
    async def _score_market_dynamics(self, token_data: Dict) -> Tuple[float, List[str], List[str]]:
        """Score REAL-TIME market dynamics and trader behavior (20 points) - Pro trader-aligned"""
        score = 0
        flags = []
        strengths = []
        print("\n[Market Dynamics & Trading Metrics Scoring]")
        try:
            # --- IMPROVED Explosive Volume Surge Detection (8 pts) ---
            # Based on experiment: need to catch surges in first 15-30 minutes
            volume_24h = token_data.get('volume_24h_usd', 0)
            volume_1h = token_data.get('volume_1h_usd', 0)
            volume_5m = token_data.get('volume_5m_usd', 0)  # Need 5-minute volume data
            market_cap = token_data.get('market_cap_usd', 1)

            # Priority 1: 5-minute volume explosion (early detection)
            if volume_5m > 0 and volume_1h > 0:
                five_min_acceleration = (volume_5m * 12) / volume_1h  # 5min * 12 = hourly rate
                if five_min_acceleration > 10:
                    score += 8
                    print("🚨 EARLY VOLUME EXPLOSION: +8 (10x+ in last 5 minutes)")
                    strengths.append("🚨 VOLUME EXPLOSION - EARLY DETECTION (10x+ surge)")
                elif five_min_acceleration > 5:
                    score += 6
                    print("Volume surge (5min): +6 (5x+ in last 5 minutes)")
                    strengths.append("🔥 Early volume surge detected (5x+)")
                elif five_min_acceleration > 3:
                    score += 4
                    print("Volume surge (5min): +4 (3x+ in last 5 minutes)")
                    strengths.append("� Strong early volume surge (3x+)")
            
            # Priority 2: Hourly acceleration (secondary indicator)
            elif volume_1h > 0 and volume_24h > 0:
                hourly_acceleration = (volume_1h * 24) / volume_24h
                if hourly_acceleration > 15:
                    score += 6
                    print("Volume acceleration: +6 (>15x in last hour - LATE but strong)")
                    strengths.append("� MASSIVE hourly volume acceleration (15x+)")
                elif hourly_acceleration > 8:
                    score += 4
                    print("Volume acceleration: +4 (>8x in last hour)")
                    strengths.append("� Strong hourly volume acceleration (8x+)")
                elif hourly_acceleration > 3:
                    score += 2
                    print("Volume acceleration: +2 (>3x in last hour)")
                    strengths.append("� Decent volume acceleration")
                else:
                    print("Volume acceleration: 0 (Insufficient surge)")
                    flags.append("weak_volume_surge")
            # --- Volume Intensity (4 pts) ---
            if market_cap > 0:
                volume_intensity = volume_24h / market_cap
                if volume_intensity > 1.2:
                    score += 4
                    print("Volume intensity: +4 (>1.2x)")
                    strengths.append("💥 INSANE VOLUME INTENSITY - Traders going crazy")
                elif volume_intensity > 0.7:
                    score += 2
                    print("Volume intensity: +2 (>0.7x)")
                    strengths.append("🔥 High volume intensity")
                elif volume_intensity > 0.3:
                    score += 1
                    print("Volume intensity: +1 (>0.3x)")
                    strengths.append("📊 Decent volume intensity")
                elif volume_intensity < 0.1:
                    print("Volume intensity: 0 (Dead volume)")
                    flags.append("dead_volume")
            # --- Price Momentum (4 pts) ---
            price_change_5m = token_data.get('price_change_5m', 0)
            price_change_15m = token_data.get('price_change_15m', 0)
            price_change_1h = token_data.get('price_change_1h', 0)
            if price_change_5m > 10:
                score += 2
                print("5m price change: +2 (>10%)")
                strengths.append("⚡ LIGHTNING PUMP - 10%+ in 5 minutes")
            if price_change_15m > 20:
                score += 1
                print("15m price change: +1 (>20%)")
                strengths.append("🔥 15m momentum - 20%+")
            if price_change_1h > 30:
                score += 1
                print("1h price change: +1 (>30%)")
                strengths.append("💎 1h pump trend - 30%+")
            # --- Whale Activity (3 pts) ---
            whale_data = token_data.get('whale_activity', {})
            large_buys_1h = whale_data.get('large_buys_1h', 0)
            large_sells_1h = whale_data.get('large_sells_1h', 0)
            if large_buys_1h > large_sells_1h * 2:
                score += 2
                print("Whale activity: +2 (Accumulation)")
                strengths.append("🐋 WHALE ACCUMULATION - Large wallets buying")
            if whale_data.get('new_large_holders_1h', 0) > 1:
                score += 1
                print("New whale entries: +1 (>1 in 1h)")
                strengths.append("🆕 New whales entering")
            # --- Liquidity/Slippage (3 pts) ---
            liquidity = token_data.get('liquidity_usd', 0)
            slippage_5k = token_data.get('slippage_5k_usd', 100)
            if liquidity > 30000 and slippage_5k < 15:
                score += 2
                print(f"Liquidity/slippage: +2 (>${liquidity:,.0f}, <15% slippage)")
                strengths.append("💧 Good liquidity - Can actually trade")
            elif liquidity > 7000 and slippage_5k < 35:
                score += 1
                print(f"Liquidity/slippage: +1 (>${liquidity:,.0f}, <35% slippage)")
                strengths.append("🌊 Adequate liquidity")
            else:
                print(f"Liquidity/slippage: 0 (High slippage or low liquidity)")
                if liquidity < 7000 or slippage_5k > 35:
                    flags.append("high_slippage")
            # --- Liquidity Growth (optional, keep) ---
            liquidity_growth = token_data.get('liquidity_growth_1h', 0)
            if liquidity_growth > 50:
                score += 1
                print("Liquidity growth: +1 (50%+ in 1h)")
                strengths.append("💧 Growing liquidity pool")
        except Exception as e:
            self.logger.error(f"Error scoring real-time market dynamics: {e}")
            flags.append("market_analysis_error")
        return score, flags, strengths
    
    async def _score_community_signals(self, token_data: Dict) -> Tuple[float, List[str], List[str]]:
        """Score REAL-TIME social momentum and hype signals (20 points) - MEME-OPTIMIZED, LENIENT VERSION"""
        score = 0
        flags = []
        strengths = []
        print("\n[Community & Social Signals Scoring]")

        try:
            social_data = token_data.get('social', {})

            # --- Twitter Mentions (up to 7 points) ---
            twitter_mentions_1h = social_data.get('twitter_mentions_1h', 0)
            if twitter_mentions_1h > 500:
                score += 7
                print("Twitter mentions: +7 (>500 in 1h)")
                strengths.append("🔥 TWITTER EXPLOSION - 500+ mentions in 1 hour")
            elif twitter_mentions_1h > 300:
                score += 6
                print("Twitter mentions: +6 (>300 in 1h)")
                strengths.append("🔥 TWITTER EXPLOSION - 300+ mentions in 1 hour")
            elif twitter_mentions_1h > 150:
                score += 5
                print("Twitter mentions: +5 (>150 in 1h)")
                strengths.append("� Strong Twitter momentum")
            elif twitter_mentions_1h > 75:
                score += 4
                print("Twitter mentions: +4 (>75 in 1h)")
                strengths.append("� Growing Twitter buzz")
            elif twitter_mentions_1h > 30:
                score += 3
                print("Twitter mentions: +3 (>30 in 1h)")
                strengths.append("� Early Twitter activity")
            elif twitter_mentions_1h > 10:
                score += 2
                print("Twitter mentions: +2 (>10 in 1h)")
                strengths.append("� Some Twitter activity")
            elif twitter_mentions_1h > 0:
                score += 1
                print("Twitter mentions: +1 (>0 in 1h)")
                strengths.append("� Any Twitter activity")

            # --- Twitter Engagement (up to 4 points) ---
            twitter_engagement_1h = social_data.get('twitter_engagement_1h', 0)
            if twitter_engagement_1h > 5000:
                score += 4
                print("Twitter engagement: +4 (>5000 in 1h)")
                strengths.append("💬 INSANE ENGAGEMENT - Real community interest")
            elif twitter_engagement_1h > 2500:
                score += 3
                print("Twitter engagement: +3 (>2500 in 1h)")
                strengths.append("💬 High engagement")
            elif twitter_engagement_1h > 1000:
                score += 2
                print("Twitter engagement: +2 (>1000 in 1h)")
                strengths.append("👥 High social engagement")
            elif twitter_engagement_1h > 300:
                score += 1
                print("Twitter engagement: +1 (>300 in 1h)")
                strengths.append("👀 Noticeable engagement")

            # --- Reddit Mentions (up to 2 points) ---
            reddit_mentions_1h = social_data.get('reddit_mentions_1h', 0)
            if reddit_mentions_1h > 20:
                score += 2
                print("Reddit mentions: +2 (>20 in 1h)")
                strengths.append("🔴 REDDIT BUZZ - Viral potential")
            elif reddit_mentions_1h > 5:
                score += 1
                print("Reddit mentions: +1 (>5 in 1h)")
                strengths.append("📱 Reddit community interest")

            # --- Telegram Activity (up to 2 points) ---
            telegram_activity_1h = social_data.get('telegram_activity_1h', 0)
            if telegram_activity_1h > 200:
                score += 2
                print("Telegram activity: +2 (>200 in 1h)")
                strengths.append("💬 TELEGRAM EXPLOSION - Community going crazy")
            elif telegram_activity_1h > 50:
                score += 1
                print("Telegram activity: +1 (>50 in 1h)")
                strengths.append("📞 Active Telegram discussion")

            # --- Influencer Mentions (up to 2 points) ---
            influencer_mentions = social_data.get('influencer_mentions_24h', 0)
            influencer_quality = social_data.get('influencer_quality', 'none')
            if influencer_quality == 'major' and influencer_mentions > 0:
                score += 2
                print("Influencer: +2 (Major)")
                strengths.append("🌟 MAJOR INFLUENCER MENTION - Potential massive pump")
            elif influencer_mentions > 0:
                score += 1
                print("Influencer: +1 (Any influencer)")
                strengths.append("👤 Some influencer mention")

            # --- Meme Viral Score (up to 2 points) ---
            meme_viral_score = social_data.get('meme_viral_score', 0)
            if meme_viral_score >= 8:
                score += 2
                print("Meme viral score: +2 (8+)")
                strengths.append("🚀 HIGH VIRAL POTENTIAL - Quality meme content")
            elif meme_viral_score >= 5:
                score += 1
                print("Meme viral score: +1 (5+)")
                strengths.append("😂 Good meme quality")

            # --- Trending Hashtags (up to 1 point) ---
            trending_hashtags = social_data.get('trending_hashtag_count', 0)
            if trending_hashtags > 0:
                score += 1
                print("Trending hashtags: +1 (>0)")
                strengths.append("📈 Trending hashtag presence")

            # --- Sentiment Momentum (up to 1 point) ---
            sentiment_momentum = social_data.get('sentiment_momentum_1h', 0)
            if sentiment_momentum > 0.1:
                score += 1
                print("Sentiment momentum: +1 (Surge)")
                strengths.append("😍 SENTIMENT SURGE - Hype building")

            # --- Growth Pattern (up to 1 point) ---
            growth_pattern = social_data.get('growth_pattern', 'unknown')
            if growth_pattern == 'viral':
                score += 1
                print("Growth pattern: +1 (Viral)")
                strengths.append("🌊 VIRAL GROWTH PATTERN")
            elif growth_pattern == 'artificial':
                print("Growth pattern: 0 (Artificial)")
                flags.append("artificial_social_growth")

        except Exception as e:
            self.logger.error(f"Error scoring social momentum: {e}")
            flags.append("social_analysis_error")

        return score, flags, strengths
    
    async def _score_technical_foundation(self, token_data: Dict) -> Tuple[float, List[str], List[str]]:
        """Score TIMING and opportunity factors (15 points) - MEME-OPTIMIZED"""
        score = 0
        flags = []
        strengths = []
        print("\n[Technical & Development Scoring]")
        
        try:
            # 🕐 DISCOVERY TIMING (8 points) - MOST CRITICAL FOR MEMES
            
            # Token age - fresher is better for memes
            creation_time = token_data.get('created_timestamp', 0)
            if creation_time > 0:
                age_hours = (time.time() - creation_time) / 3600
                age_days = age_hours / 24
                if age_hours < 1:  # Brand new (within 1 hour)
                    score += 4
                    print("Token age: +4 (<1h)")
                    strengths.append("🆕 ULTRA-FRESH - Less than 1 hour old")
                elif age_hours < 6:  # Very early (within 6 hours)
                    score += 3
                    print("Token age: +3 (<6h)")
                    strengths.append("⚡ Very early discovery - Under 6 hours")
                elif age_hours < 24:  # Early (within 1 day)
                    score += 2
                    print("Token age: +2 (<24h)")
                    strengths.append("🌅 Early discovery - Under 24 hours")
                elif age_days < 7:  # Still early (within 1 week)
                    score += 1
                    print("Token age: +1 (<7d)")
                    strengths.append("📅 Recent launch - Under 1 week")
                elif age_days > 30:  # Getting old for memes
                    print("Token age: 0 (>30d)")
                    flags.append("old_token")
            
            # Exchange listing status - pre-listing is golden
            listing_data = token_data.get('listings', {})
            major_cex_listed = listing_data.get('major_cex', False)
            small_cex_listed = listing_data.get('small_cex', False)
            dex_only = not major_cex_listed and not small_cex_listed
            
            if dex_only:
                score += 3
                print("Exchange listing: +3 (DEX only)")
                strengths.append("💎 DEX-ONLY - Pre-CEX pump potential")
            elif small_cex_listed and not major_cex_listed:
                score += 1
                print("Exchange listing: +1 (Small CEX)")
                strengths.append("🏪 Small CEX listed - Room for major exchange pump")
            else:
                print("Exchange listing: 0 (Already mainstream)")
                flags.append("already_mainstream")

            # Influencer discovery stage
            influencer_coverage = token_data.get('influencer_coverage', 'none')
            if influencer_coverage == 'none':
                score += 1
                print("Influencer coverage: +1 (None)")
                strengths.append("📢 Pre-influencer discovery - High upside potential")
            elif influencer_coverage == 'emerging':
                score += 0.5
                print("Influencer coverage: +0.5 (Emerging)")
            
            # 📊 MARKET OPPORTUNITY (4 points) - SIZE THE OPPORTUNITY
            
            market_cap = token_data.get('market_cap_usd', 0)
            
            # Market cap sweet spot for meme pumps
            if 1000 <= market_cap <= 100000:  # $1k-100k sweet spot
                score += 3
                print(f"Market cap: +3 (${market_cap:,.0f})")
                strengths.append("🎯 PERFECT MARKET CAP - Huge pump potential")
            elif 100000 <= market_cap <= 1000000:  # $100k-1M still good
                score += 2
                print(f"Market cap: +2 (${market_cap:,.0f})")
                strengths.append("💰 Good market cap for growth")
            elif 1000000 <= market_cap <= 10000000:  # $1M-10M getting expensive
                score += 1
                print(f"Market cap: +1 (${market_cap:,.0f})")
                strengths.append("📈 Moderate growth potential")
            elif market_cap > 50000000:  # Above $50M is getting heavy
                print(f"Market cap: 0 (High: ${market_cap:,.0f})")
                flags.append("high_market_cap")
            
            # Holder count - fewer holders = more room to grow
            holder_count = token_data.get('holder_count', 999999)
            if holder_count < 100:  # Very few holders
                score += 1
                print(f"Holder count: +1 ({holder_count} holders)")
                strengths.append("👥 Low holder count - Room for massive growth")
            elif holder_count > 10000:  # Too many holders already
                print(f"Holder count: 0 (Saturated: {holder_count})")
                flags.append("saturated_holders")
            
            # 🔄 MOMENTUM INDICATORS (3 points) - CATCH THE WAVE
            
            # Recent activity surge
            activity_surge = token_data.get('activity_surge_24h', False)
            if activity_surge:
                score += 2
                print("Activity surge: +2 (24h)")
                strengths.append("🌊 ACTIVITY SURGE - Momentum building")
            
            # Smart money wallets detected
            smart_money_interest = token_data.get('smart_money_wallets', 0)
            if smart_money_interest > 3:  # Smart money is buying
                score += 1
                print("Smart money: +1 (Accumulating)")
                strengths.append("🧠 Smart money accumulating")

            # --- Dev Activity (up to 1 point) ---
            dev_activity = token_data.get('project', {}).get('development_activity', {})
            if isinstance(dev_activity, dict):
                if dev_activity.get('github_commits', '') == 'active' or dev_activity.get('regular_updates', False):
                    score += 1
                    print("Dev activity: +1 (Active development)")
                    strengths.append("💻 Active development - Regular updates")

            # --- Website/Docs/Transparency (up to 1 point) ---
            project_info = token_data.get('project', {})
            if project_info.get('website_quality', '') == 'professional':
                score += 2
                print("Website: +2 (Professional)")
                strengths.append("🌐 Professional website")
            elif project_info.get('website_quality', '') == 'basic':
                score += 1
                print("Website: +1 (Basic)")
                strengths.append("🌐 Basic website")
                
            if project_info.get('documentation_quality', '') in ['basic', 'clear', 'detailed']:
                score += 2
                print("Docs: +2 (Has docs)")
                strengths.append("📄 Has documentation")
            
            if project_info.get('team_public', False):
                score += 1
                print("Team: +1 (Public team)")
                strengths.append("👤 Public team")

            # --- Partnerships/Utility (up to 1 point) ---
            if project_info.get('has_partnerships', False):
                score += 1
                print("Partnerships: +1 (Has partnerships)")
                strengths.append("🤝 Partnerships announced")
                
            if project_info.get('utility', '') not in ['', 'none', 'planned']:
                score += 0.5
                print("Utility: +0.5 (Has utility)")
                strengths.append("🔧 Has real utility")

            # --- Negative flags for missing transparency (small deductions) ---
            if not project_info.get('website_quality'):
                score -= 0.25
                print("Website: -0.25 (No website)")
                flags.append("no_website")
            if not project_info.get('documentation_quality'):
                score -= 0.25
                print("Docs: -0.25 (No docs)")
                flags.append("no_docs")
            if not project_info.get('roadmap_quality'):
                score -= 0.25
                print("Roadmap: -0.25 (No roadmap)")
                flags.append("no_roadmap")

        except Exception as e:
            self.logger.error(f"Error scoring timing and opportunity: {e}")
            flags.append("timing_analysis_error")
            
        return score, flags, strengths
    
    async def _score_timing_factors(self, token_data: Dict, market_context: Optional[Dict]) -> Tuple[float, List[str], List[str]]:
        """Score REAL-TIME market timing and momentum (10 points) - MEME-OPTIMIZED"""
        score = 0
        flags = []
        strengths = []
        print("\n[Timing & Market Context Scoring]")
        
        try:
            # 📈 MARKET MOMENTUM (5 points) - RIDE THE WAVE
            
            # Overall Solana/meme market sentiment
            if market_context:
                solana_performance = market_context.get('solana_24h_change', 0)
                if solana_performance > 5:  # SOL pumping helps memes
                    score += 2
                    print("Solana perf: +2 (>5%)")
                    strengths.append("🚀 Solana pumping - Meme coin favorable environment")
                elif solana_performance > 0:
                    score += 1
                    print("Solana perf: +1 (>0%)")
                    strengths.append("📈 Positive Solana momentum")
                elif solana_performance < -10:
                    print("Solana perf: 0 (<-10%)")
                    flags.append("solana_dumping")
                
                # Meme coin sector performance
                meme_sector_momentum = market_context.get('meme_sector_24h', 0)
                if meme_sector_momentum > 20:  # Meme sector exploding
                    score += 2
                    print("Meme sector: +2 (>20%)")
                    strengths.append("💥 MEME SECTOR EXPLOSION - Perfect timing")
                elif meme_sector_momentum > 0:
                    score += 1
                    print("Meme sector: +1 (>0%)")
                    strengths.append("🎭 Meme coins trending")
                
                # Fear & Greed for memes
                market_greed = market_context.get('fear_greed_index', 50)
                if market_greed > 70:  # High greed = meme pumps
                    score += 1
                    print("Fear/Greed: +1 (>70)")
                    strengths.append("🤑 Market greed high - Meme pump season")
            
            # ⚡ IMMEDIATE TIMING SIGNALS (5 points) - RIGHT NOW FACTORS
            
            # Time of day optimization (crypto markets are 24/7 but have patterns)
            current_hour_utc = datetime.utcnow().hour
            # Peak activity times for memes (US + EU overlap)
            if 12 <= current_hour_utc <= 20:  # 12-8 PM UTC (8AM-4PM EST)
                score += 1
                print("Trading hour: +1 (Peak)")
                strengths.append("⏰ Peak trading hours - Maximum attention")
            elif 8 <= current_hour_utc <= 12 or 20 <= current_hour_utc <= 24:
                score += 0.5
                print("Trading hour: +0.5 (Good)")
                strengths.append("🕐 Good trading hours")
            
            # Weekend vs weekday (weekends can be wild for memes)
            current_weekday = datetime.utcnow().weekday()
            if current_weekday >= 5:  # Saturday or Sunday
                score += 1
                print("Weekend: +1 (Sat/Sun)")
                strengths.append("🎉 Weekend pump potential - Lower volume, higher volatility")
            
            # Recent major token launches (competition factor)
            recent_major_launches = token_data.get('recent_major_launches_24h', 0)
            if recent_major_launches == 0:  # No competition
                score += 2
                print("Major launches: +2 (None)")
                strengths.append("🎯 Clear market - No major launches competing for attention")
            elif recent_major_launches > 3:  # Too much competition
                print("Major launches: 0 (Crowded)")
                flags.append("crowded_launch_day")
            
            # Social media trending cycles
            trending_peak = token_data.get('trending_momentum', 'none')
            if trending_peak == 'building':
                score += 1
                print("Trending momentum: +1 (Building)")
                strengths.append("📊 Trending momentum building")
            elif trending_peak == 'peak':
                score += 0.5  # Might be late
                print("Trending momentum: +0.5 (Peak)")
                strengths.append("🔥 At trending peak")
            elif trending_peak == 'fading':
                print("Trending momentum: 0 (Fading)")
                flags.append("momentum_fading")
                
        except Exception as e:
            self.logger.error(f"Error scoring timing factors: {e}")
            flags.append("timing_analysis_error")
        
        return score, flags, strengths
    
    async def _score_risk_factors(self, token_data: Dict, existing_flags: List[str]) -> Tuple[float, List[str]]:
        """Assess risk factors and calculate deductions"""
        deductions = 0
        risk_flags = []
        print("\n[Risk Deductions]")
        
        try:
            # Warning signal deductions
            if 'weak_social_presence' in existing_flags or 'small_community' in existing_flags:
                deductions += 3
                print("Social presence: -3 (Weak or small community)")
                risk_flags.append("minimal_social_presence")
            
            # Excessive marketing claims
            marketing_claims = token_data.get('marketing_analysis', {})
            if marketing_claims.get('excessive_claims', False):
                deductions += 2
                print("Marketing claims: -2 (Excessive)")
                risk_flags.append("excessive_marketing")
            
            # Copy-paste detection
            if token_data.get('is_copycat', False):
                deductions += 2
                print("Copycat: -2 (Copycat project)")
                risk_flags.append("copycat_project")
            
            # Suspicious whale movements
            whale_activity = token_data.get('whale_activity', {})
            if whale_activity.get('suspicious_movements', False):
                deductions += 2
                print("Whale activity: -2 (Suspicious movements)")
                risk_flags.append("suspicious_whale_activity")
            
            # Poor community engagement
            engagement_score = token_data.get('engagement_score', 50)  # 0-100 scale
            if engagement_score < 20:
                deductions += 1
                print("Engagement: -1 (Poor engagement)")
                risk_flags.append("poor_engagement")
                
        except Exception as e:
            self.logger.error(f"Error assessing risk factors: {e}")
            risk_flags.append("risk_assessment_error")
        
        return deductions, risk_flags
    
    def _apply_market_adjustments(self, base_score: float, category_scores: Dict, 
                                market_context: Dict) -> float:
        """Apply market condition adjustments to scoring"""
        try:
            market_condition = market_context.get('condition', 'sideways')
            weights = self.MARKET_CONDITION_WEIGHTS.get(market_condition, {})
            
            # Apply category-specific weights
            adjusted_score = base_score
            for category, weight in weights.items():
                if category in category_scores:
                    adjustment = (category_scores[category] * weight) - category_scores[category]
                    adjusted_score += adjustment
            
            return min(100, max(0, adjusted_score))
            
        except Exception as e:
            self.logger.error(f"Error applying market adjustments: {e}")
            return base_score
    
    def _determine_tier(self, score: float) -> str:
        """Determine tier based on total score"""
        if score >= self.TIER_THRESHOLDS['A']:
            return 'A'
        elif score >= self.TIER_THRESHOLDS['B']:
            return 'B'
        elif score >= self.TIER_THRESHOLDS['C']:
            return 'C'
        else:
            return 'D'
    
    def _generate_recommendation(self, tier: str, score: float, 
                               red_flags: List[str], strengths: List[str]) -> str:
        """Generate meme trading recommendation based on real-time analysis"""
        if tier == 'A':
            return f"🚀 MEME PUMP ALERT - Score: {score:.1f}/100. Strong signals detected - Act fast! Potential 200-1000% gains."
        elif tier == 'B':
            return f"📈 STRONG BUY - Score: {score:.1f}/100. Good momentum building - Enter with caution. Target 100-500% gains."
        elif tier == 'C':
            return f"👀 WATCH CLOSELY - Score: {score:.1f}/100. Early signals present - Small position only. Target 50-200% gains."
        else:
            return f"❌ AVOID - Score: {score:.1f}/100. Too many risks or no momentum detected."
    
    def _assess_risk_level(self, score: float, red_flags: List[str]) -> str:
        """Assess overall risk level"""
        critical_count = len([f for f in red_flags if f in self.CRITICAL_RED_FLAGS])
        
        if critical_count > 0:
            return "CRITICAL"
        elif score < 30 or len(red_flags) > 5:
            return "HIGH"
        elif score < 60 or len(red_flags) > 2:
            return "MEDIUM"
        else:
            return "LOW"

    def format_detailed_analysis(self, result: ScoringResult, token_symbol: str) -> str:
        """Format detailed meme analysis for logging/reporting"""
        analysis = f"""
🚀 MEME COIN ANALYSIS: {token_symbol}
{'='*50}

📊 PUMP SCORE: {result.total_score:.1f}/100 (Tier {result.tier})
⚡ RISK LEVEL: {result.risk_level}
🎯 SIGNAL: {result.recommendation}

� REAL-TIME ANALYSIS:
• Trading Safety: {result.category_scores.get('on_chain_health', 0):.1f}/25
• Volume & Momentum: {result.category_scores.get('market_dynamics', 0):.1f}/20  
• Social Hype: {result.category_scores.get('community_signals', 0):.1f}/20
• Timing & Opportunity: {result.category_scores.get('technical_foundation', 0):.1f}/15
• Market Timing: {result.category_scores.get('timing_factors', 0):.1f}/10
• Risk Penalties: -{result.category_scores.get('risk_deductions', 0):.1f}

✅ PUMP SIGNALS:
{chr(10).join(f'  🔥 {strength}' for strength in result.strengths[:5]) if result.strengths else '  • No pump signals detected'}

⚠️ WARNING SIGNS:
{chr(10).join(f'  ❌ {flag.replace("_", " ").title()}' for flag in result.red_flags[:5]) if result.red_flags else '  • No major risks detected'}

{'='*50}
        """
        return analysis.strip()
    
    def should_send_signal_comprehensive(self, comprehensive_result, speculative_mode=False) -> bool:

        """
        Determine if a comprehensive analysis should trigger a signal.
        
        Args:
            comprehensive_result: ScoringResult object from comprehensive_score method
        Returns:
            Boolean indicating if signal should be sent
        """
        if not comprehensive_result:
            return False
        # Handle both ScoringResult object and dict
        if hasattr(comprehensive_result, 'total_score'):
            score = comprehensive_result.total_score
            tier = comprehensive_result.tier
        else:
            # Fallback for dict format
            score = comprehensive_result.get('comprehensive_score', 0)
            tier = comprehensive_result.get('tier', 'D')
        
        # Signal criteria based on tier system - configurable via environment
        if tier == 'A' and self.SIGNAL_CRITERIA['tier_a_always']:  # Default: Always signal A-tier
            return True
        elif tier == 'B' and score >= self.SIGNAL_CRITERIA['tier_b_min_score']:  # Default: B-tier if score >= 40
            return True
        elif tier == 'C' and score >= self.SIGNAL_CRITERIA['tier_c_min_score']:  # Default: C-tier if score >= 25
            return True
        elif speculative_mode and self.is_speculative_candidate(comprehensive_result):
            return True
        elif tier == 'D' and not self.SIGNAL_CRITERIA['tier_d_never']:
            return score >= 40
        return False

    def get_position_size_recommendation(self, comprehensive_result) -> str:
        """
        Get position size recommendation based on comprehensive analysis.
        
        Args:
            comprehensive_result: ScoringResult object from comprehensive_score method
            
        Returns:
            Position size recommendation string
        """
        if not comprehensive_result:
            return "NO POSITION"
        
        # Handle both ScoringResult object and dict
        if hasattr(comprehensive_result, 'total_score'):
            tier = comprehensive_result.tier
            score = comprehensive_result.total_score
        else:
            # Fallback for dict format
            tier = comprehensive_result.get('tier', 'D')
            score = comprehensive_result.get('comprehensive_score', 0)
        
        if tier == 'A':
            if score >= 90:
                return "5-8% of portfolio"
            else:
                return "3-5% of portfolio"
        elif tier == 'B':
            return "1-3% of portfolio"
        elif tier == 'C':
            return "0.5-1% of portfolio (speculation only)"
        else:
            return "NO POSITION"

    def get_tp_sl_position(self, current_price, comprehensive_result) -> str:
        """
        Get take profit and stop loss position based on comprehensive analysis.

        Args:
            comprehensive_result: ScoringResult object from comprehensive_score method
            
        Returns:
            Position size recommendation string
        """
        
        tier = comprehensive_result.get('tier', 'D')
        
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
    
        target_1_price = current_price * (1 + target_1_percent / 100) if current_price > 0 else 0
        target_2_price = current_price * (1 + target_2_percent / 100) if current_price > 0 else 0
        stop_loss_price = current_price * (1 + stop_loss_percent / 100) if current_price > 0 else 0
        
        return {
            'target_1_percent': target_1_percent,
            'target_2_percent': target_2_percent,
            'target_1_price': target_1_price,
            'target_2_price': target_2_price,
            'stop_loss_price': stop_loss_price,
            'stop_loss_percent': stop_loss_percent,
        }

# Usage example and testing
if __name__ == "__main__":
    async def demo_comprehensive_scorer():
        scorer = ComprehensiveTokenScorer()
        
        # Example token data
        test_token = {
            'symbol': 'TESTMEME',
            'liquidity': {'usd': 150000, 'locked': True, 'lock_duration_days': 365},
            'contract': {'verified': True, 'ownership': 'renounced'},
            'honeypot_check': {'is_honeypot': False},
            'holders': {'top_10_percentage': 25},
            'dev_allocation_percentage': 3,
            'volume_24h_usd': 75000,
            'market_cap_usd': 500000,
            'transactions_24h': 800,
            'holder_growth_24h_percentage': 15,
            'price_analysis': {'trend': 'strong_uptrend', 'volatility': 'healthy', 'has_structure': True},
            'social': {
                'telegram_members': 3000,
                'twitter_followers': 5000,
                'discord_activity': 'high',
                'reddit_mentions': 50,
                'growth_pattern': 'organic'
            },
            'meme_analysis': {
                'quality_score': 7,
                'cultural_relevance': 'relevant',
                'originality': 'unique',
                'creative_marketing': True
            },
            'project': {
                'website_quality': 'professional',
                'documentation_quality': 'basic',
                'roadmap_quality': 'clear',
                'team_public': True,
                'utility': 'planned',
                'has_partnerships': False,
                'development_activity': {'github_commits': 'active', 'regular_updates': True}
            },
            'listings': {'major_cex': False, 'small_cex': False},
            'influencer_coverage': 'none',
            'created_timestamp': time.time() - (3 * 86400)  # 3 days old
        }
        
        market_context = {
            'crypto_sentiment': 'bullish',
            'meme_cycle_position': 'early',
            'positive_catalysts': True,
            'condition': 'bull_market'
        }
        
        result = await scorer.comprehensive_score(test_token, market_context)
        print(scorer.format_detailed_analysis(result, test_token['symbol']))
        
    # Run demo
    asyncio.run(demo_comprehensive_scorer())
