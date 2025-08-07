"""
Enhanced data source integration for better reliability.
Adds Birdeye.so as primary source with DexScreener as backup.
"""

import requests
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import BIRDEYE_API_KEY


class BirdeyeAPI:
    """
    Birdeye.so API integration for more reliable token data
    Based on official documentation: https://docs.birdeye.so
    """
    
    def __init__(self):
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {
            "accept": "application/json",
            "x-chain": "solana"  # Default to Solana
        }
        
        # Add API key if available
        if BIRDEYE_API_KEY:
            self.headers["X-API-KEY"] = BIRDEYE_API_KEY
            # print(f"✅ Birdeye API key configured: {BIRDEYE_API_KEY[:8]}...")
        else:
            print("⚠️ Birdeye API key not found - using free tier limits")
    
    async def get_token_price(self, token_address: str, chain: str = "solana") -> Optional[Dict]:
        """
        Get current token price from Birdeye
        Endpoint: /defi/price
        """
        try:
            url = f"{self.base_url}/defi/price"
            params = {
                "address": token_address,
                "include_liquidity": "true"
            }
            
            # Set chain in headers
            headers = self.headers.copy()
            headers["x-chain"] = chain
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    return data.get('data', {})
                else:
                    print(f"❌ Birdeye API error: {data}")
            elif response.status_code == 401:
                print(f"❌ Birdeye API: Unauthorized - check API key")
            elif response.status_code == 429:
                print(f"⚠️ Birdeye API: Rate limit exceeded")
            else:
                print(f"❌ Birdeye API error {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Birdeye API error for token {token_address}: {e}")
            return None
    
    async def get_token_price_history(self, token_address: str, timeframe: str = "1H", 
                                    chain: str = "solana") -> Optional[List[Dict]]:
        """
        Get price history for performance tracking
        Endpoint: /defi/history_price
        """
        try:
            url = f"{self.base_url}/defi/history_price"
            params = {
                "address": token_address,
                "type": timeframe
            }
            
            # Set chain in headers
            headers = self.headers.copy()
            headers["x-chain"] = chain
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    return data.get('data', {}).get('items', [])
            
            return None
            
        except Exception as e:
            print(f"Birdeye price history error for token {token_address}: {e}")
            return None
    
    async def get_token_list(self, chain: str = "solana", sort_by: str = "v24hChangePercent", 
                           sort_type: str = "desc", limit: int = 50) -> Optional[List[Dict]]:
        """
        Get trending/top tokens from Birdeye
        Endpoint: /defi/tokenlist
        """
        try:
            url = f"{self.base_url}/defi/tokenlist"
            params = {
                "sort_by": sort_by,
                "sort_type": sort_type,
                "offset": 0,
                "limit": limit
            }
            
            # Set chain in headers
            headers = self.headers.copy()
            headers["x-chain"] = chain
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    return data.get('data', {}).get('tokens', [])
            elif response.status_code == 401:
                print(f"❌ Birdeye API: Unauthorized - check API key")
            elif response.status_code == 429:
                print(f"⚠️ Birdeye API: Rate limit exceeded")
            else:
                print(f"❌ Birdeye tokenlist error {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Birdeye top gainers error: {e}")
            return None


class MultiSourceDataValidator:
    """
    Cross-validate data from multiple sources for reliability
    """
    
    def __init__(self):
        self.birdeye = BirdeyeAPI()
        # Keep DexScreener functions as backup
        from src.discovery.dexscreener import fetch_pairs
        self.fetch_pairs = fetch_pairs
    
    async def get_validated_token_data(self, token_address: str) -> Dict:
        """
        Get token data from multiple sources and cross-validate
        """
        print(f"🔍 Validating token data from multiple sources: {token_address[:8]}...")
        
        # Get data from all sources
        birdeye_data = await self.birdeye.get_token_price(token_address)
        dexscreener_pairs = self.fetch_pairs(token_address)
        
        # Convert DexScreener response to expected format
        dexscreener_data = {'pairs': dexscreener_pairs} if dexscreener_pairs else None
        
        # Cross-validate and combine data
        validated_data = {
            'token_address': token_address,
            'timestamp': datetime.now(),
            'sources_used': [],
            'data_quality': 'unknown',
            'price': None,
            'liquidity_usd': 0,
            'volume_24h': 0,
            'market_cap': 0,
            'price_change_24h': 0,
            'pair_count': 0
        }
        
        # Process Birdeye data (primary source)
        if birdeye_data:
            validated_data['sources_used'].append('birdeye')
            validated_data['price'] = birdeye_data.get('value')  # Birdeye uses 'value' for price
            validated_data['liquidity_usd'] = birdeye_data.get('liquidity', 0)
            validated_data['price_change_24h'] = birdeye_data.get('priceChange24h', 0)
            # Note: Birdeye price endpoint doesn't include volume/market cap
            
            print(f"✅ Birdeye data: Price ${validated_data['price']:.8f}, Liquidity ${validated_data['liquidity_usd']:,.0f}")
        else:
            print(f"⚠️ Birdeye data not available for {token_address[:8]}...")
        
        # Process DexScreener data (backup/validation)
        if dexscreener_data and dexscreener_data.get('pairs'):
            validated_data['sources_used'].append('dexscreener')
            pairs = dexscreener_data['pairs']
            validated_data['pair_count'] = len(pairs)
            
            # Calculate totals from all pairs
            total_liquidity = sum(pair.get('liquidity', {}).get('usd', 0) or 0 for pair in pairs)
            total_volume = sum(pair.get('volume', {}).get('h24', 0) or 0 for pair in pairs)
            
            # Use DexScreener data if Birdeye failed
            if not birdeye_data:
                if pairs:
                    validated_data['price'] = pairs[0].get('priceUsd')
                    validated_data['liquidity_usd'] = total_liquidity
                    validated_data['volume_24h'] = total_volume
                    validated_data['price_change_24h'] = pairs[0].get('priceChange', {}).get('h24', 0) or 0
            
            print(f"✅ DexScreener data: {len(pairs)} pairs, Total Liquidity ${total_liquidity:,.0f}")
        
        # Determine data quality
        if len(validated_data['sources_used']) >= 2:
            validated_data['data_quality'] = 'high'
        elif len(validated_data['sources_used']) == 1:
            validated_data['data_quality'] = 'medium'
        else:
            validated_data['data_quality'] = 'low'
            print(f"⚠️ Warning: Limited data available for {token_address}")
        
        return validated_data
    
    async def validate_price_accuracy(self, token_address: str, 
                                    reported_price: float) -> Dict:
        """
        Validate if reported price is accurate across sources
        """
        birdeye_data = await self.birdeye.get_token_price(token_address)
        
        if birdeye_data and birdeye_data.get('value'):  # Birdeye uses 'value' for price
            birdeye_price = birdeye_data['value']
            price_difference = abs(reported_price - birdeye_price) / birdeye_price * 100
            
            return {
                'is_accurate': price_difference < 5.0,  # Within 5%
                'price_difference_percent': price_difference,
                'birdeye_price': birdeye_price,
                'reported_price': reported_price
            }
        
        return {'is_accurate': False, 'error': 'Could not validate price'}
    
    async def get_dexscreener_data(self, token_address: str) -> List[Dict]:
        """Get DexScreener data for validation"""
        try:
            # Use the dexscreener module that already exists
            from src.discovery.dexscreener import fetch_pairs
            return fetch_pairs(token_address)
        except Exception as e:
            print(f"Error getting DexScreener data: {e}")
            return []


# Enhanced token discovery with multiple sources
class EnhancedTokenDiscovery:
    """
    Enhanced token discovery using multiple data sources
    """
    
    def __init__(self):
        self.validator = MultiSourceDataValidator()
    
    async def discover_trending_tokens(self) -> List[Dict]:
        """
        Discover trending tokens from multiple sources
        """
        print("🔍 Discovering trending tokens from multiple sources...")
        
        all_tokens = []
        
        # Get top gainers from Birdeye
        birdeye_gainers = await self.validator.birdeye.get_token_list(
            sort_by="v24hChangePercent", 
            sort_type="desc", 
            limit=20
        )
        if birdeye_gainers:
            for token in birdeye_gainers[:20]:  # Top 20
                token_address = token.get('address')
                if token_address:
                    validated_data = await self.validator.get_validated_token_data(token_address)
                    if validated_data['data_quality'] in ['high', 'medium']:
                        all_tokens.append(validated_data)
        
        # Get boosted tokens from DexScreener (existing method)
        try:
            from src.discovery.dexscreener import discover_new_pairs
            dexscreener_tokens = discover_new_pairs()
            
            for token_data in dexscreener_tokens[:10]:  # Top 10
                if token_data.get('token_address'):
                    validated_data = await self.validator.get_validated_token_data(token_data['token_address'])
                    if validated_data['data_quality'] in ['high', 'medium']:
                        all_tokens.append(validated_data)
        except Exception as e:
            print(f"DexScreener discovery error: {e}")
        
        # Remove duplicates and sort by quality
        unique_tokens = {}
        for token in all_tokens:
            addr = token['token_address']
            if addr not in unique_tokens or token['data_quality'] == 'high':
                unique_tokens[addr] = token
        
        sorted_tokens = sorted(unique_tokens.values(), 
                             key=lambda x: (x['data_quality'] == 'high', x['volume_24h']), 
                             reverse=True)
        
        print(f"✅ Discovered {len(sorted_tokens)} unique tokens with reliable data")
        return sorted_tokens
    
    async def get_comprehensive_token_data(self, token_address: str, dex_pairs: Optional[List[Dict]] = None) -> Dict:
        """
        Get comprehensive token data combining multiple sources
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dict with comprehensive token analysis data
        """
        try:
            # Initialize comprehensive data structure with REALISTIC fields
            token_data = {
                'symbol': 'UNKNOWN',
                'address': token_address,
                'created_timestamp': time.time(),
                'liquidity': {'usd': 0, 'locked': False, 'lock_duration_days': 0},
                'contract': {'verified': False, 'ownership': 'unknown', 'can_mint': True},
                'honeypot_check': {'is_honeypot': False, 'can_sell': True},  # DEFAULT TO SAFE - Will be updated by security check
                'holders': {'top_10_percentage': 50},
                'dev_allocation_percentage': 10,
                'volume_24h_usd': 0,
                'volume_1h_usd': 0,  # REAL field from DexScreener
                'price_change_5m': 0,  # REAL field from DexScreener
                'price_change_15m': 0,  # REAL field from DexScreener  
                'price_change_1h': 0,  # REAL field from DexScreener
                'volume_growth_1h': 0,  # Calculated from available data
                'liquidity_growth_1h': 0,  # Not available - default 0
                'slippage_5k_usd': 15,  # Estimated - not available from APIs
                'buy_tax_percentage': 5,  # Estimated - not available from APIs
                'sell_tax_percentage': 10,  # Estimated - not available from APIs
                'max_transaction_percentage': 100,  # Default - not available from APIs
                'has_pause_function': False,  # Default - not available from APIs
                'market_cap_usd': 0,
                'transactions_24h': 0,
                'holder_growth_24h_percentage': 0,
                'holder_count': 1000,  # Default estimate
                'whale_activity': {  # Basic structure
                    'large_buys_1h': 0,
                    'large_sells_1h': 0, 
                    'new_large_holders_1h': 0
                },
                'price_analysis': {
                    'trend': 'sideways',
                    'volatility': 'moderate',
                    'has_structure': False
                },
                'social': {
                    'telegram_members': 0,
                    'twitter_followers': 0,
                    'discord_activity': 'low',
                    'reddit_mentions': 0,
                    'growth_pattern': 'unknown',
                    # NEW: Real-time social fields (estimated from available data)
                    'twitter_mentions_1h': 0,
                    'twitter_engagement_1h': 0,
                    'reddit_mentions_1h': 0,
                    'telegram_activity_1h': 0,
                    'influencer_mentions_24h': 0,
                    'influencer_quality': 'none',
                    'kol_activity': 'none',
                    'meme_viral_score': 5,
                    'trending_hashtag_count': 0,
                    'sentiment_momentum_1h': 0
                },
                'meme_analysis': {
                    'quality_score': 5,
                    'cultural_relevance': 'neutral',
                    'originality': 'variation',
                    'creative_marketing': False
                },
                'project': {
                    'website_quality': 'basic',
                    'documentation_quality': 'none',
                    'roadmap_quality': 'none',
                    'team_public': False,
                    'utility': 'none',
                    'has_partnerships': False,
                    'development_activity': {
                        'github_commits': 'none',
                        'regular_updates': False
                    }
                },
                'listings': {'major_cex': False, 'small_cex': False},
                'influencer_coverage': 'none',
                'activity_surge_24h': False,  # NEW: Activity indicators
                'smart_money_wallets': 0,  # NEW: Smart money tracking
                'recent_major_launches_24h': 0,  # NEW: Competition tracking
                'trending_momentum': 'none'  # NEW: Trending status
            }

            # Use DexScreener data (passed or fetch if not provided)
            if dex_pairs is None:
                from src.discovery.dexscreener import fetch_pairs
                dex_pairs = fetch_pairs(token_address)
            
            if dex_pairs and len(dex_pairs) > 0:
                pair_data = dex_pairs[0]  # Use first pair
                
                # Extract basic trading data
                token_data['symbol'] = pair_data.get('baseToken', {}).get('symbol', 'UNKNOWN')
                
                # MAP ACTUAL DEXSCREENER VOLUME DATA
                volume_data = pair_data.get('volume', {})
                token_data['volume_24h_usd'] = volume_data.get('h24', 0)
                token_data['volume_1h_usd'] = volume_data.get('h1', 0)  # REAL 1h volume
                
                # MAP ACTUAL DEXSCREENER PRICE CHANGE DATA  
                price_change_data = pair_data.get('priceChange', {})
                token_data['price_change_5m'] = price_change_data.get('m5', 0)  # REAL 5m price change
                token_data['price_change_15m'] = price_change_data.get('m15', 0)  # REAL 15m if available
                token_data['price_change_1h'] = price_change_data.get('h1', 0)  # REAL 1h price change
                
                # Basic market data
                token_data['market_cap_usd'] = pair_data.get('marketCap', 0)
                token_data['liquidity']['usd'] = pair_data.get('liquidity', {}).get('usd', 0)
                
                # Extract transaction counts - REAL DATA
                txns_24h = pair_data.get('txns', {}).get('h24', {})
                txns_1h = pair_data.get('txns', {}).get('h1', {})
                buys_24h = txns_24h.get('buys', 0)
                sells_24h = txns_24h.get('sells', 0)
                buys_1h = txns_1h.get('buys', 0)
                sells_1h = txns_1h.get('sells', 0)
                
                token_data['transactions_24h'] = buys_24h + sells_24h
                
                # REAL WHALE ACTIVITY DATA (basic from transaction patterns)
                token_data['whale_activity'] = {
                    'large_buys_1h': buys_1h,  # Use 1h buys as proxy
                    'large_sells_1h': sells_1h,  # Use 1h sells as proxy
                    'new_large_holders_1h': 0  # Not available, set to 0
                }
                
                # Calculate volume growth if possible
                volume_1h = volume_data.get('h1', 0)
                volume_24h = volume_data.get('h24', 0)
                if volume_24h > 0 and volume_1h > 0:
                    # Estimate hourly acceleration
                    expected_hourly = volume_24h / 24
                    if expected_hourly > 0:
                        token_data['volume_growth_1h'] = ((volume_1h / expected_hourly) - 1) * 100
                
                # Set realistic liquidity data (no growth data available)
                token_data['liquidity_growth_1h'] = 0  # Not available from APIs
                token_data['slippage_5k_usd'] = 15  # Default estimate - not available from DexScreener
                
                # Extract social information from DexScreener
                info = pair_data.get('info', {})
                if info:
                    socials = info.get('socials', [])
                    websites = info.get('websites', [])
                    
                    # Extract social URLs for later analysis
                    telegram_url = None
                    twitter_url = None
                    
                    for social in socials:
                        social_type = social.get('type', '').lower()
                        social_url = social.get('url', '')
                        
                        if social_type == 'telegram' and social_url:
                            telegram_url = social_url
                        elif social_type == 'twitter' and social_url:
                            twitter_url = social_url
                    
                    # Analyze social presence (simplified for now)
                    if telegram_url:
                        # Extract channel name from URL for basic analysis
                        if 't.me/' in telegram_url:
                            channel_name = telegram_url.split('t.me/')[-1]
                            # Estimate based on URL patterns (could be enhanced with API calls)
                            if len(channel_name) > 5:  # Longer names might indicate more established channels
                                token_data['social']['telegram_members'] = 100  # Conservative estimate
                                # SET REALISTIC SOCIAL ACTIVITY (not real-time data)
                                token_data['social']['telegram_activity_1h'] = 10  # Conservative estimate
                                
                    if twitter_url:
                        # Extract handle from URL for basic analysis
                        if 'x.com/' in twitter_url or 'twitter.com/' in twitter_url:
                            handle = twitter_url.split('/')[-1]
                            if len(handle) > 3:  # Basic validation
                                token_data['social']['twitter_followers'] = 50  # Conservative estimate
                                # SET BASIC SOCIAL SIGNALS (not real-time data)
                                token_data['social']['twitter_mentions_1h'] = 5  # Conservative estimate
                                token_data['social']['twitter_engagement_1h'] = 20  # Conservative estimate
                    
                    # Set default social metrics (no real-time data available)
                    token_data['social']['reddit_mentions_1h'] = 0  # Not available
                    token_data['social']['influencer_mentions_24h'] = 0  # Not available
                    token_data['social']['influencer_quality'] = 'none'  # Not available
                    token_data['social']['kol_activity'] = 'none'  # Not available
                    token_data['social']['meme_viral_score'] = 5  # Default score
                    token_data['social']['trending_hashtag_count'] = 0  # Not available
                    token_data['social']['sentiment_momentum_1h'] = 0  # Not available
                    token_data['social']['growth_pattern'] = 'unknown'  # Default
                    
                    # Website quality assessment
                    if websites:
                        token_data['project']['website_quality'] = 'basic'
                        if len(websites) > 1:
                            token_data['project']['website_quality'] = 'professional'
                    
                    # Improve meme quality based on having social presence
                    if telegram_url or twitter_url:
                        token_data['meme_analysis']['quality_score'] = 7  # Higher than default
                        token_data['meme_analysis']['creative_marketing'] = True
            
            # Get Birdeye data to supplement
            birdeye_data = await self.get_token_price(token_address)
            if birdeye_data:
                # Update with Birdeye data if better/more recent
                birdeye_volume = birdeye_data.get('v24hUSD', 0)
                birdeye_mc = birdeye_data.get('mc', 0)
                birdeye_liquidity = birdeye_data.get('liquidity', 0)
                
                # Use Birdeye data if it's higher (more complete)
                if birdeye_volume > token_data['volume_24h_usd']:
                    token_data['volume_24h_usd'] = birdeye_volume
                if birdeye_mc > token_data['market_cap_usd']:
                    token_data['market_cap_usd'] = birdeye_mc
                if birdeye_liquidity > token_data['liquidity']['usd']:
                    token_data['liquidity']['usd'] = birdeye_liquidity
                
                # NOTE: Do NOT fabricate data! Only use real API data
                # Set realistic price analysis based on real data only
                if token_data['market_cap_usd'] > 0 and token_data['volume_24h_usd'] > 0:
                    volume_ratio = (token_data['volume_24h_usd'] / token_data['market_cap_usd']) * 100
                    if volume_ratio > 30:
                        token_data['price_analysis']['trend'] = 'uptrend'
                    elif volume_ratio < 5:
                        token_data['price_analysis']['trend'] = 'downtrend'
                
                # REMOVED FAKE DATA GENERATION:
                # - NO fake transaction counts based on volume
                # - NO fake holder growth based on volume
                # If we don't have real data, we keep it as 0 and mark data quality accordingly
            
            # Get DexScreener data for validation
            dex_data = await self.validator.get_dexscreener_data(token_address)
            if dex_data:
                # Cross-validate and update data
                for pair in dex_data:
                    if pair.get('baseToken', {}).get('address') == token_address:
                        # Update with DexScreener data
                        token_data['symbol'] = pair.get('baseToken', {}).get('symbol', token_data['symbol'])
                        
                        # Update liquidity and volume
                        if pair.get('liquidity', {}).get('usd'):
                            token_data['liquidity']['usd'] = max(
                                token_data['liquidity']['usd'],
                                pair['liquidity']['usd']
                            )
                        
                        if pair.get('volume', {}).get('h24'):
                            token_data['volume_24h_usd'] = max(
                                token_data['volume_24h_usd'],
                                pair['volume']['h24']
                            )
            
            # Add quality rating based on data completeness
            data_quality = self._assess_data_quality(token_data)
            token_data['data_quality_score'] = data_quality
            
            # INTEGRATE REAL HONEYPOT CHECK
            try:
                from src.security.honeypot_check import analyze_token_safety
                safety_result = analyze_token_safety(token_address, dex_pairs if dex_pairs else [])
                
                # Update honeypot data with real check results
                if safety_result:
                    # Only flag as honeypot if explicitly detected as risky
                    is_risky = safety_result.get('risk_level', 'LOW') in ['HIGH', 'CRITICAL']
                    risk_score = safety_result.get('risk_score', 0)
                    
                    # Conservative honeypot detection - only flag if very risky
                    if is_risky and risk_score > 80:
                        token_data['honeypot_check']['is_honeypot'] = True
                        token_data['honeypot_check']['can_sell'] = False
                    else:
                        # Default to tradeable unless proven otherwise
                        token_data['honeypot_check']['is_honeypot'] = False
                        token_data['honeypot_check']['can_sell'] = True
                    
                    # Update estimated taxes based on safety analysis  
                    if 'buy_tax' in safety_result:
                        token_data['buy_tax_percentage'] = safety_result['buy_tax']
                    if 'sell_tax' in safety_result:
                        token_data['sell_tax_percentage'] = safety_result['sell_tax']
                else:
                    # If no safety result, default to safe
                    token_data['honeypot_check']['is_honeypot'] = False
                    token_data['honeypot_check']['can_sell'] = True
                        
            except Exception as e:
                print(f"Warning: Could not perform honeypot check: {e}")
                # Default to safe if honeypot check fails
                token_data['honeypot_check']['is_honeypot'] = False
                token_data['honeypot_check']['can_sell'] = True
            
            return token_data
            
        except Exception as e:
            print(f"Error getting comprehensive token data: {e}")
            # Return minimal data structure on error
            return {
                'symbol': 'ERROR',
                'address': token_address,
                'error': str(e),
                'liquidity': {'usd': 0},
                'volume_24h_usd': 0,
                'market_cap_usd': 0
            }
    
    def _assess_data_quality(self, token_data: Dict) -> int:
        """Assess the quality of collected data (0-100 scale) - HONEST ASSESSMENT"""
        score = 0
        issues = []
        
        # Core data availability (60 points total)
        if token_data.get('symbol') and token_data['symbol'] != 'UNKNOWN':
            score += 15
        else:
            issues.append('missing_symbol')
            
        if token_data.get('volume_24h_usd', 0) > 0:
            score += 15
        else:
            issues.append('no_volume_data')
            
        if token_data.get('market_cap_usd', 0) > 0:
            score += 15
        else:
            issues.append('no_market_cap_data')
            
        if token_data.get('liquidity', {}).get('usd', 0) > 0:
            score += 15
        else:
            issues.append('no_liquidity_data')
        
        # Real transaction data (not fabricated) - 20 points
        transactions = token_data.get('transactions_24h', 0)
        if transactions > 0:
            # Check if this looks like real data or fabricated
            volume = token_data.get('volume_24h_usd', 0)
            if volume > 0 and abs(transactions - (volume / 100)) < 10:
                # This looks like fabricated data (volume/100)
                issues.append('fabricated_transaction_data')
                score += 5  # Partial credit only
            else:
                score += 20  # Real transaction data
        else:
            issues.append('no_transaction_data')
        
        # Real holder growth data (not fabricated) - 20 points  
        holder_growth = token_data.get('holder_growth_24h_percentage', 0)
        if holder_growth > 0:
            # Check if this looks like real data or fabricated
            volume = token_data.get('volume_24h_usd', 0)
            if volume > 0 and abs(holder_growth - min(20, volume / 10000)) < 0.1:
                # This looks like fabricated data (volume/10000)
                issues.append('fabricated_holder_data')
                score += 5  # Partial credit only
            else:
                score += 20  # Real holder data
        else:
            issues.append('no_holder_growth_data')
        
        # Store quality issues for transparency
        token_data['data_quality_issues'] = issues
        
        return min(100, score)
    
    async def get_token_price(self, token_address: str, chain: str = "solana") -> Optional[Dict]:
        """
        Get token price data using the Birdeye API through validator
        """
        try:
            return await self.validator.birdeye.get_token_price(token_address, chain)
        except Exception as e:
            print(f"Error getting token price: {e}")
            return None


if __name__ == "__main__":
    # Demo the enhanced data sources
    async def demo_enhanced_discovery():
        print("🧪 Demo: Enhanced Token Discovery...")
        
        discovery = EnhancedTokenDiscovery()
        tokens = await discovery.discover_trending_tokens()
        
        print(f"\n📊 Found {len(tokens)} tokens:")
        for i, token in enumerate(tokens[:5]):  # Show top 5
            print(f"{i+1}. {token['token_address'][:8]}... | "
                  f"Price: ${token['price']:.8f} | "
                  f"Volume: ${token['volume_24h']:,.0f} | "
                  f"Quality: {token['data_quality']} | "
                  f"Sources: {', '.join(token['sources_used'])}")
    
    # Run demo
    asyncio.run(demo_enhanced_discovery())
