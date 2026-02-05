import sys
from risk_regime_bro import market_data, risk_engine

def main() -> None:
    print("--- Risk Regime Bro ---")
    
    # 1. Define Universe
    buckets = market_data.get_bucket_symbols()
    all_symbols = []
    for syms in buckets.values():
        all_symbols.extend(syms)
        
    print(f"Tracking {len(all_symbols)} assets across {len(buckets)} buckets.")
    
    # 2. Fetch Data
    print("Fetching market data from CoinGecko... (1h, 24h, 7d)")
    symbols_to_fetch = list(set(all_symbols + ["bitcoin"]))
    
    full_data_map = market_data.fetch_historical_prices(symbols_to_fetch)
    
    if not full_data_map:
        print("Failed to fetch data.")
        return

    print("\n" + "="*60)
    print(f"{'TIMEFRAME':<10} {'RISK':<10} {'REGIME'}")
    print("="*60)

    timeframes = ['1h', '24h', '7d']
    
    for tf in timeframes:
        # Slice data for this timeframe
        current_map = {}
        for sym, windows in full_data_map.items():
            if tf in windows:
                current_map[sym] = windows[tf]
        
        btc_data = current_map.get("bitcoin")
        if not btc_data:
            print(f"{tf:<10} N/A        (Missing BTC data)")
            continue
            
        results = risk_engine.calculate_risk_metrics(current_map, btc_data, buckets)
        regime = results['Regime']['Full']
        risk_val = results['RISK']
        
        # Color/Intensity Formatting (Text-based)
        print(f"{tf:<10} {risk_val:<10.4f} {regime}")
        
    print("="*60 + "\n")
    
    # Detailed Breakdown for 24h (Standard Pulse)
    print("--- 24h Deep Dive ---")
    
    # Re-extract 24h for detail print
    tf_24 = '24h'
    map_24 = {s: w[tf_24] for s, w in full_data_map.items() if tf_24 in w}
    btc_24 = map_24.get("bitcoin")
    
    if btc_24:
        results = risk_engine.calculate_risk_metrics(map_24, btc_24, buckets)
        intensities = results['Intensities']
        
        print(f"Risk Level:     {intensities['RiskLevel']}")
        print(f"Participation:  {intensities['Participation']}")
        print(f"Structure:      {intensities['Structure']}")
        print()
        print(f"Breadth:    {results['Breadth_total']:.2%}")
        print(f"Spec Conc:  {results['SpecConc']:.2f}")
        print(f"BTC Return: {results['BTC_Return']:.2%}")
        
        print("\nBucket Breakdown:")
        print(f"{'Bucket':<15} {'Score (weighted)':<20} {'Raw Q'}")
        print("-" * 45)
        
        for bucket, res in results['Buckets'].items():
            print(f"{bucket:<15} {res['wQ']:<20.4f} {res['Q_b']:.4f}")

    print("\nDone.")

if __name__ == "__main__":
    main()
