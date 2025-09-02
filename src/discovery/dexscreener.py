import requests
import sys
import os

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import CHAIN_ID


# DexScreener API URLs
LATEST_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"  # Latest created tokens (FRESH!)
BOOSTS_URL = "https://api.dexscreener.com/token-boosts/latest/v1"  # OLD: Boosted tokens (already trending)
TOKEN_PAIRS_URL = "https://api.dexscreener.com/token-pairs/v1"

def fetch_latest_tokens():
    """
    NEW METHOD: Fetch latest token profiles - these are FRESH tokens creating profiles.
    Much earlier than boosted/trending tokens!
    """
    latest_api_res = requests.get(LATEST_PROFILES_URL)
    latest_api_res.raise_for_status()

    # all_tokens = [t["tokenAddress"] for t in boosted_api_res.json()]
    all_tokens = [t["tokenAddress"] for t in latest_api_res.json()]
    
    # Filter tokens by blockchain format
    if CHAIN_ID == "solana":
        # Solana addresses are 44 characters and don't start with 0x
        solana_tokens = [token for token in all_tokens 
                        if not token.startswith('0x') and len(token) > 30]
        print(f"🆕 Total latest profile tokens: {len(all_tokens)}")
        print(f"🎯 Solana latest tokens: {len(solana_tokens)}")
        return solana_tokens
    else:
        # For other chains, return all tokens
        return all_tokens

# OLD METHOD - COMMENTED OUT (was getting already trending tokens)
# def fetch_boosted_tokens():
#     boosted_api_res = requests.get(BOOSTS_URL)
#     boosted_api_res.raise_for_status()
#     all_tokens = [t["tokenAddress"] for t in boosted_api_res.json()]
#     if CHAIN_ID == "solana":
#         solana_tokens = [token for token in all_tokens 
#                         if not token.startswith('0x') and len(token) > 30]
#         print(f"🔍 Total boosted tokens: {len(all_tokens)}")
#         print(f"🎯 Solana boosted tokens: {len(solana_tokens)}")
#         return solana_tokens
#     else:
#         return all_tokens

def fetch_pairs(token_address: str) -> list[dict]:
    """
    Given a token address, fetch all active trading pairs for that token on the specified chain.
    
    Args:
        token_address: A Solana token mint address (string).
    Returns:
        List of dicts, each representing a pair, containing fields like:
        - pairAddress (string)
        - liquidity: { "usd": float, ... }
        - volume: { "usd": float, ... }
        - priceUsd, pairCreatedAt, etc.
    Raises:
        HTTPError if API request fails.
    """
    try:
        print(f"🔍 Fetching pairs for token: {CHAIN_ID} {token_address}")
        url = f"{TOKEN_PAIRS_URL}/{CHAIN_ID}/{token_address}"
        resp = requests.get(url)
        resp.raise_for_status()
        result = resp.json()  # This is a list directly, not {"pairs": [...]}
        return result if isinstance(result, list) else []
    except requests.RequestException as e:
        print(f"Error fetching pairs for {token_address}: {e}")
        return []

def discover_new_pairs() -> list[dict]:
    """
    Discover new token pairs based on LATEST token profiles on Solana.
    This gets FRESH tokens creating profiles, not already trending ones!
    
    Returns:
        Combined list of pair dictionaries for each latest token,
        with liquidity and volume information included.
    """
    # NEW METHOD: Use latest token profiles (fresh launches)
    latest_tokens = fetch_latest_tokens()  
    all_pairs = []
    for addr in latest_tokens:
        print(f"🆕 Fetching pairs for latest token: {addr}")
        pairs = fetch_pairs(addr)
        print(f"🔍 Found {len(pairs)} pairs for token {addr}")
        if pairs:  # Only extend if pairs is not None or empty
            all_pairs.extend(pairs)
    
    # OLD METHOD - COMMENTED FOR ROLLBACK
    # boosted_tokens = fetch_boosted_tokens()
    # all_pairs = []
    # for addr in boosted_tokens:
    #     print(f"🔍 Fetching pairs for boosted token: {addr}")
    #     pairs = fetch_pairs(addr)
    #     print(f"🔍 Found {len(pairs)} pairs for token {addr}")
    #     if pairs:  # Only extend if pairs is not None or empty
    #         all_pairs.extend(pairs)
    
    return all_pairs

if __name__ == "__main__":
    pairs = discover_new_pairs()
    print(f"🔍 Total Solana pairs discovered: {len(pairs)}")
    for p in pairs[:5]:
        addr = p.get("pairAddress")
        liq = p.get("liquidity", {}).get("usd")
        vol = p.get("volume", {}).get("usd")
        print(f"Pair {addr} — Liquidity: ${liq}, Volume: ${vol}")
