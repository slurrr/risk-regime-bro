import requests
import pandas as pd
from typing import Dict, List, Optional
import time

# Static Bucket Definitions (as per success.md requirements roughly mapped to current market)
BUCKETS = {
    "majors": ["ethereum", "solana", "binancecoin"],
    "large": ["ripple", "cardano", "avalanche-2", "polkadot"],
    "mid": ["aptos", "sui", "sei-network", "arbitrum"],
    "high_beta": ["pepe", "dogwifhat", "bonk", "floki"], # Using popular high betas
    "memes": ["dogecoin", "shiba-inu"] # Legacy memes
}

# Combine high_beta and memes for the "Memes" bucket in the spec if needed, 
# or keep them separate. The spec lists: Majors, Large, Mid, High beta, Memes.
# Let's align exactly with spec buckets.
# Spec: Majors, Large alts, Midcaps, High beta / perp-driven, Memes.

# Refined mapping based on current market (approximate)
BUCKET_MAPPING = {
    "majors": ["ethereum", "solana", "binancecoin"],
    "large_alts": ["ripple", "cardano", "avalanche-2", "near", "polkadot"],
    "midcaps": ["aptos", "sui", "arbitrum", "optimism", "sei-network"],
    "high_beta": ["pepe", "dogwifhat", "bonk"], # Often behave like memes but "high beta"
    "memes": ["dogecoin", "shiba-inu", "popcat", "morg-2"] # Pure memes
}

def get_bucket_symbols() -> Dict[str, List[str]]:
    return BUCKET_MAPPING

def fetch_current_prices(symbols: List[str]) -> Dict[str, float]:
    """
    Fetches current prices for a list of symbols from CoinGecko.
    
    Args:
        symbols: List of CoinGecko API IDs.
        
    Returns:
        Dictionary mapping symbol to price.
    """
    if not symbols:
        return {}
    
    # CoinGecko allows multiple IDs comma separated
    ids_str = ",".join(symbols)
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ids_str,
        "vs_currencies": "usd"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        for sym in symbols:
            if sym in data:
                prices[sym] = data[sym]["usd"]
        return prices
    except Exception as e:
        print(f"Error fetching current prices: {e}")
        return {}

def fetch_historical_prices(symbols: List[str], days: int = 1) -> Dict[str, float]:
    """
    Fetches historical prices (L days ago) to calculate returns.
    Since CoinGecko simple/price doesn't give historical, we might need 
    coins/{id}/market_chart or similar. 
    However, to save API calls, we can try to estimate or fetch differently.
    
    Strategy: For each coin, fetch O,H,L,C or just price N days ago.
    CoinGecko market_chart endpoint: coins/{id}/market_chart?vs_currency=usd&days={days}
    This is heavy (1 call per coin).
    
    Alternative for 'lookback L': 
    If L is small (e.g. 24h), we can use 'price_change_percentage_24h' from 
    'coins/markets' endpoint which is ONE call for many coins. 
    
    The spec asks for: ln(P(t)/P(t-L)).
    If L=24h, P(t)/P(t-L) = 1 + pct_change_24h/100.
    
    Let's assume L=24h for the default 'Risk Regime' calculation as it's the standard daily pulse.
    """
    
    # We will use coins/markets to get 1h, 24h, 7d changes for all symbols in one go.
    ids_str = ",".join(symbols)
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids_str,
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d" 
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Structure: symbol -> time_window -> {'current':, 'prev':}
        # Windows: '1h', '24h', '7d'
        result = {}
        
        for item in data:
            sym = item['id']
            current_price = item['current_price']
            
            if current_price is None:
                continue
                
            # CoinGecko keys for percentages:
            # price_change_percentage_1h_in_currency
            # price_change_percentage_24h (sometimes just this) or _in_currency
            # price_change_percentage_7d_in_currency
            
            windows = {
                '1h': item.get('price_change_percentage_1h_in_currency'),
                '24h': item.get('price_change_percentage_24h'), # Standard field
                '7d': item.get('price_change_percentage_7d_in_currency')
            }
            
            sym_data = {}
            for window, pct_change in windows.items():
                if pct_change is None:
                    # Fallback or skip. If missing 1h, maybe just set prev=current (0% change)
                    prev_price = current_price
                else:
                    prev_price = current_price / (1 + pct_change / 100.0)
                
                sym_data[window] = {
                    "current": current_price,
                    "prev": prev_price
                }
            
            result[sym] = sym_data
            
        return result
        
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return {}

def fetch_btc_price_data() -> Dict[str, float]:
    """Convenience for just BTC."""
    data = fetch_historical_prices(["bitcoin"])
    if "bitcoin" in data:
        return data["bitcoin"]
    return {"current": 0.0, "prev": 0.0}
