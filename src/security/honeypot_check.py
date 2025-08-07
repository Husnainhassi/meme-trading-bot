"""
Honeypot detection module for Solana tokens.
Checks for common red flags that indicate a token might be a honeypot or scam.
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import CHAIN_ID


class HoneypotChecker:
    """
    Analyzes Solana tokens for honeypot and rug pull risks.
    """
    
    def __init__(self):
        self.risk_score_weights = {
            'liquidity_too_low': 30,
            'high_concentration': 25,
            'new_token': 20,
            'suspicious_trading': 15,
            'low_holder_count': 10
        }
    
    def check_token_risk(self, token_address: str, pair_data: List[Dict]) -> Dict:
        """
        Comprehensive risk assessment for a token.
        
        Args:
            token_address: The Solana token mint address
            pair_data: List of trading pairs from DexScreener
            
        Returns:
            Dict containing:
            - risk_score: 0-100 (higher = more risky)
            - risk_level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            - flags: List of detected risk factors
            - details: Detailed analysis
        """
        if not pair_data:
            return {
                'risk_score': 100,
                'risk_level': 'CRITICAL',
                'flags': ['NO_PAIRS_FOUND'],
                'details': 'No trading pairs found for this token',
                'is_safe': False
            }
        
        # Validate pair data structure
        if not self._validate_pair_data(pair_data):
            print("Warning: Some pair data may be incomplete or malformed")
        
        risk_score = 0
        flags = []
        details = {}
        
        # Check liquidity
        liquidity_risk, liquidity_flags = self._check_liquidity(pair_data)
        risk_score += liquidity_risk
        flags.extend(liquidity_flags)
        
        # Check token age
        age_risk, age_flags = self._check_token_age(pair_data)
        risk_score += age_risk
        flags.extend(age_flags)
        
        # Check trading patterns
        trading_risk, trading_flags = self._check_trading_patterns(pair_data)
        risk_score += trading_risk
        flags.extend(trading_flags)
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = 'CRITICAL'
        elif risk_score >= 60:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Calculate details with error handling
        try:
            total_liquidity = 0
            max_liquidity = 0
            for pair in pair_data:
                try:
                    liq_usd = pair.get('liquidity', {}).get('usd', 0)
                    if liq_usd is not None:
                        liq_value = float(liq_usd)
                        total_liquidity += liq_value
                        max_liquidity = max(max_liquidity, liq_value)
                except (TypeError, ValueError):
                    continue
                    
            details = {
                'total_pairs': len(pair_data),
                'total_liquidity': total_liquidity,
                'max_liquidity': max_liquidity
            }
        except Exception as e:
            print(f"Warning: Error calculating details: {e}")
            details = {
                'total_pairs': len(pair_data),
                'total_liquidity': 0,
                'max_liquidity': 0,
                'calculation_error': str(e)
            }
        
        return {
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'flags': flags,
            'details': details
        }
    
    def _validate_pair_data(self, pair_data: List[Dict]) -> bool:
        """
        Validate that pair data contains expected fields.
        
        Args:
            pair_data: List of trading pairs
            
        Returns:
            Boolean indicating if data structure is valid
        """
        if not pair_data:
            return False
        
        required_fields = ['liquidity', 'volume']
        optional_fields = ['pairCreatedAt', 'pairAddress']
        
        valid_pairs = 0
        for pair in pair_data:
            if not isinstance(pair, dict):
                continue
                
            # Check for required fields
            has_required = all(field in pair for field in required_fields)
            if has_required:
                valid_pairs += 1
        
        # Consider data valid if at least 50% of pairs have required fields
        return valid_pairs >= len(pair_data) * 0.5
    
    def _check_liquidity(self, pair_data: List[Dict]) -> Tuple[int, List[str]]:
        """Check liquidity-related risks."""
        risk_score = 0
        flags = []
        
        try:
            # Calculate total and max liquidity with better error handling
            liquidity_values = []
            for pair in pair_data:
                try:
                    liq_usd = pair.get('liquidity', {}).get('usd', 0)
                    if liq_usd is not None:
                        liquidity_values.append(float(liq_usd))
                    else:
                        liquidity_values.append(0.0)
                except (TypeError, ValueError):
                    liquidity_values.append(0.0)
            
            total_liquidity = sum(liquidity_values)
            max_liquidity = max(liquidity_values) if liquidity_values else 0
            
            # Very low total liquidity
            if total_liquidity < 1000:
                risk_score += self.risk_score_weights['liquidity_too_low']
                flags.append('VERY_LOW_LIQUIDITY')
            elif total_liquidity < 5000:
                risk_score += self.risk_score_weights['liquidity_too_low'] // 2
                flags.append('LOW_LIQUIDITY')
            
            # Check for liquidity concentration in single pair
            if len(pair_data) > 1 and total_liquidity > 0 and max_liquidity > total_liquidity * 0.9:
                risk_score += self.risk_score_weights['high_concentration']
                flags.append('LIQUIDITY_CONCENTRATED')
                
        except Exception as e:
            print(f"Warning: Error in liquidity analysis: {e}")
            # If we can't analyze liquidity, treat as high risk
            risk_score += self.risk_score_weights['liquidity_too_low']
            flags.append('LIQUIDITY_ANALYSIS_FAILED')
        
        return risk_score, flags
    
    def _check_token_age(self, pair_data: List[Dict]) -> Tuple[int, List[str]]:
        """Check token age related risks."""
        risk_score = 0
        flags = []
        
        # Find oldest pair creation time
        oldest_pair = None
        current_time = time.time()
        
        for pair in pair_data:
            created_at = pair.get('pairCreatedAt')
            if created_at:
                try:
                    parsed_timestamp = self._parse_timestamp(created_at)
                    if parsed_timestamp is not None:
                        pair_age_hours = (current_time - parsed_timestamp) / 3600
                        
                        if oldest_pair is None or pair_age_hours > oldest_pair:
                            oldest_pair = pair_age_hours
                except (ValueError, TypeError, KeyError) as e:
                    print(f"Warning: Error processing timestamp for pair: {e}")
                    continue
        
        if oldest_pair is not None:
            # Very new token (less than 1 hour)
            if oldest_pair < 1:
                risk_score += self.risk_score_weights['new_token']
                flags.append('VERY_NEW_TOKEN')
            elif oldest_pair < 24:  # Less than 1 day
                risk_score += self.risk_score_weights['new_token'] // 2
                flags.append('NEW_TOKEN')
        
        return risk_score, flags
    
    def _parse_timestamp(self, timestamp) -> Optional[float]:
        """
        Parse timestamp from various formats to Unix timestamp in seconds.
        
        Args:
            timestamp: Timestamp in various formats (int, float, string)
            
        Returns:
            Unix timestamp in seconds, or None if parsing fails
        """
        try:
            if isinstance(timestamp, str):
                # Try parsing ISO format or other string formats
                from datetime import datetime
                try:
                    # Try ISO format first
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return dt.timestamp()
                except:
                    # Try parsing as numeric string
                    timestamp = float(timestamp)
            
            if isinstance(timestamp, (int, float)):
                # Handle both seconds and milliseconds
                if timestamp > 1e10:  # Likely milliseconds (after year 2001)
                    return timestamp / 1000
                else:  # Likely seconds
                    return timestamp
            
            return None
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Could not parse timestamp {timestamp}: {e}")
            return None
    
    def _check_trading_patterns(self, pair_data: List[Dict]) -> Tuple[int, List[str]]:
        """Check for suspicious trading patterns."""
        risk_score = 0
        flags = []
        
        # Check volume to liquidity ratios
        for pair in pair_data:
            try:
                liquidity = pair.get('liquidity', {}).get('usd', 0) or 0
                volume_24h = pair.get('volume', {}).get('h24', 0) or 0
                
                if liquidity > 0 and volume_24h > 0:
                    volume_ratio = volume_24h / liquidity
                    
                    # Suspiciously high volume compared to liquidity
                    if volume_ratio > 10:
                        risk_score += self.risk_score_weights['suspicious_trading']
                        flags.append('HIGH_VOLUME_RATIO')
                        break
                    # Suspiciously low volume
                    elif volume_ratio < 0.01:
                        risk_score += self.risk_score_weights['suspicious_trading'] // 2
                        flags.append('LOW_VOLUME_RATIO')
                        break
            except (TypeError, KeyError, ZeroDivisionError) as e:
                print(f"Warning: Error analyzing trading patterns for pair: {e}")
                continue
        
        return risk_score, flags
    
    def is_safe_to_trade(self, risk_assessment: Dict) -> bool:
        """
        Determine if a token is safe enough to trade based on risk assessment.
        
        Args:
            risk_assessment: Output from check_token_risk()
            
        Returns:
            Boolean indicating if token is safe to trade
        """
        return risk_assessment['risk_level'] in ['LOW', 'MEDIUM']
    
    def get_recommended_action(self, risk_assessment: Dict) -> str:
        """
        Get recommended action based on risk assessment.
        
        Args:
            risk_assessment: Output from check_token_risk()
            
        Returns:
            String with recommended action
        """
        risk_level = risk_assessment['risk_level']
        
        if risk_level == 'LOW':
            return "✅ SAFE TO TRADE - Low risk detected"
        elif risk_level == 'MEDIUM':
            return "⚠️ PROCEED WITH CAUTION - Medium risk, small position recommended"
        elif risk_level == 'HIGH':
            return "🚨 HIGH RISK - Avoid or use very small position"
        else:  # CRITICAL
            return "🛑 DO NOT TRADE - Critical risk factors detected"


def analyze_token_safety(token_address: str, pair_data: List[Dict]) -> Dict:
    """
    Convenience function to analyze token safety.
    
    Args:
        token_address: The Solana token mint address
        pair_data: List of trading pairs from DexScreener
        
    Returns:
        Complete risk assessment with recommendations
    """
    checker = HoneypotChecker()
    risk_assessment = checker.check_token_risk(token_address, pair_data)
    
    # Add recommendations
    risk_assessment['is_safe'] = checker.is_safe_to_trade(risk_assessment)
    risk_assessment['recommendation'] = checker.get_recommended_action(risk_assessment)
    
    return risk_assessment


if __name__ == "__main__":
    # Test the honeypot checker
    from src.discovery.dexscreener import fetch_pairs, fetch_boosted_tokens
    
    print("🔒 Testing Honeypot Checker...")
    
    # Get a few boosted tokens for testing
    boosted_tokens = fetch_boosted_tokens()[:3]
    
    for token_addr in boosted_tokens:
        print(f"\n📊 Analyzing token: {token_addr}")
        pairs = fetch_pairs(token_addr)
        
        if pairs:
            risk_assessment = analyze_token_safety(token_addr, pairs)
            
            print(f"Risk Score: {risk_assessment['risk_score']}/100")
            print(f"Risk Level: {risk_assessment['risk_level']}")
            print(f"Recommendation: {risk_assessment['recommendation']}")
            print(f"Flags: {', '.join(risk_assessment['flags']) if risk_assessment['flags'] else 'None'}")
            print(f"Total Liquidity: ${risk_assessment['details']['total_liquidity']:,.2f}")
        else:
            print("❌ No pairs found for this token")
