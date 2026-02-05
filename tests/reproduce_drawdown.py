from risk_regime_bro import risk_engine

# Mock Data
# Scenario: Global Dump, but Alts outperform BTC (drop less).
# BTC: -10%
# Majors: -5%
# Mid: -5%
# Memes: -2%

# Prices: 100 -> 90 (BTC), 100 -> 95 (Alts)

btc_data = {"current": 90, "prev": 100}

# Populate standard buckets
buckets = {
    "majors": ["eth", "sol"],
    "large_alts": ["ada", "avax"],
    "midcaps": ["sui", "apt"],
    "high_beta": ["pepe"],
    "memes": ["doge"]
}

market_data = {
    "bitcoin": btc_data,
    # Majors down 12% (Underperforming BTC -10%)
    "eth": {"current": 88, "prev": 100}, 
    "sol": {"current": 88, "prev": 100},
    # Large down 12%
    "ada": {"current": 88, "prev": 100},
    "avax": {"current": 88, "prev": 100},
    # Mid down 12%
    "sui": {"current": 88, "prev": 100},
    "apt": {"current": 88, "prev": 100},
    # Memes down 8% (Outperforming BTC -10%)
    "pepe": {"current": 88, "prev": 100}, # High Beta follows Majors (-12%)
    "doge": {"current": 95, "prev": 100}  # Pure Meme pumps (only -5%)
}

print("Running Divergence Simulation (BTC -10%, Majors -12%, Doge -5%)...")
print(f"BTC Change: {(90/100)-1:.1%}")

results = risk_engine.calculate_risk_metrics(market_data, btc_data, buckets)

print("\n--- RESULTS ---")
print(f"RISK: {results['RISK']:.4f}")
print(f"Regime: {results['Regime']['Full']}")
print(f"Risk Level: {results['Intensities']['RiskLevel']}")
print("---------------")
