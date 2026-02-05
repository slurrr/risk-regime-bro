import numpy as np
import math
from typing import Dict, List, Any

# Weights from spec
# Majors w=1
# Large alts w=2
# Midcaps w=3
# High beta w=4
# Memes w=5
BUCKET_WEIGHTS = {
    "majors": 1.0,
    "large_alts": 2.0,
    "midcaps": 3.0,
    "high_beta": 4.0,
    "memes": 5.0
}

def calculate_log_return(current: float, prev: float) -> float:
    if prev == 0:
        return 0.0
    return math.log(current / prev)

def calculate_risk_metrics(
    market_data: Dict[str, Dict[str, float]], 
    btc_data: Dict[str, float],
    buckets: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Calculates the Risk Regime metrics.
    
    Args:
        market_data: Dict mapping symbol -> {'current': float, 'prev': float}
        btc_data: Dict {'current': float, 'prev': float}
        buckets: Dict mapping bucket_name -> [symbols]
        
    Returns:
        Dict containing raw metrics, bucket scores, and semantic labels.
    """
    
    # 1. BTC Return
    btc_ret = calculate_log_return(btc_data['current'], btc_data['prev'])
    
    # 2. Per-symbol relative performance (r_i)
    # r_i = ln(P_i(t)/P_i(t-L)) - ln(P_BTC(t)/P_BTC(t-L))
    #     = Return_i - Return_BTC
    
    r_i_map = {}
    
    for sym, data in market_data.items():
        if sym == 'bitcoin': continue
        
        curr = data['current']
        prev = data['prev']
        
        sym_ret = calculate_log_return(curr, prev)
        r_i = sym_ret - btc_ret
        r_i_map[sym] = r_i

    # 3. Bucket level strength + breadth
    bucket_results = {}
    total_weighted_risk = 0.0
    
    # For global breadth calculation
    total_alts_count = 0
    total_alts_outperforming = 0
    
    # For speculative concentration calculation: SpecConc = w_meme * Q_meme / sum(|w_b * Q_b|)
    sum_abs_weighted_q = 0.0
    meme_weighted_q = 0.0
    
    for bucket_name, symbols in buckets.items():
        # Filter symbols that we actually have data for
        valid_syms = [s for s in symbols if s in r_i_map]
        
        if not valid_syms:
            bucket_results[bucket_name] = {
                "S_b": 0.0,
                "B_b": 0.0,
                "Q_b": 0.0
            }
            continue
            
        # Strength: S_b = mean(r_i)
        S_b = np.mean([r_i_map[s] for s in valid_syms])
        
        # Breadth: B_b = mean(1 if r_i > 0 else 0)
        B_b = np.mean([1.0 if r_i_map[s] > 0 else 0.0 for s in valid_syms])
        
        # Bucket Score: Q_b = S_b * (2 * B_b - 1)
        # BUG FIX: success.md formula `S * (2B - 1)` flips sign if S is negative and B is low (0).
        # Standard interpretation: 
        # - If S > 0 (Outperformance), we penalize narrow breadth (Pos * Neg = Neg).
        # - If S < 0 (Underperformance), we do NOT want to flip to positive. 
        #   We just take the raw underperformance or maybe penalize broadness differently.
        #   For now, strictly preserving sign for S < 0.
        
        if S_b >= 0:
            Q_b = S_b * (2 * B_b - 1)
        else:
            # If negative strength, allow it to be negative. 
            # Could optionally partial-scale if breadth is mixed, but raw S_b is safest.
            Q_b = S_b
        
        weight = BUCKET_WEIGHTS.get(bucket_name, 1.0)
        weighted_Q = weight * Q_b
        
        bucket_results[bucket_name] = {
            "S_b": S_b,
            "B_b": B_b,
            "Q_b": Q_b,
            "wQ": weighted_Q
        }
        
        total_weighted_risk += weighted_Q
        sum_abs_weighted_q += abs(weighted_Q)
        
        if bucket_name == "memes":
            meme_weighted_q = weighted_Q
            
        # Global stats
        total_alts_count += len(valid_syms)
        total_alts_outperforming += sum(1 for s in valid_syms if r_i_map[s] > 0)

    # 4. Final Metric (RISK)
    RISK = total_weighted_risk
    
    # Auxiliary metrics
    breadth_total = 0.0
    if total_alts_count > 0:
        breadth_total = total_alts_outperforming / total_alts_count
        
    spec_conc = 0.0
    if sum_abs_weighted_q > 0:
        spec_conc = meme_weighted_q / sum_abs_weighted_q
        
    # Semantic Translation
    # Step 1: Component Intensities
    intensity_labels = get_intensity_labels(RISK, breadth_total, spec_conc)
    
    # Step 2 & 3: Archetypes & Modifiers
    regime = translate_regime(RISK, breadth_total, spec_conc, bucket_results)
    
    return {
        "RISK": RISK,
        "Breadth_total": breadth_total,
        "SpecConc": spec_conc,
        "BTC_Return": btc_ret,
        "Buckets": bucket_results,
        "Regime": regime,
        "Intensities": intensity_labels
    }

def get_intensity_labels(risk: float, breadth: float, spec_conc: float) -> Dict[str, str]:
    """
    Step 1 of Translation Layer: Convert numbers to semantic intensities.
    """
    # Risk Level
    if risk > 0.5: risk_label = "Full Send"
    elif risk > 0.05: risk_label = "Risk On"
    elif risk >= -0.05: risk_label = "Chop / Indecision"
    elif risk >= -0.5: risk_label = "Risk Off"
    else: risk_label = "Capitulation Mode"
    
    # Breadth
    if breadth >= 0.6: breadth_label = "Broad"
    elif breadth >= 0.3: breadth_label = "Selective"
    else: breadth_label = "Narrow"
    
    # Speculation Location
    if spec_conc >= 0.6: spec_label = "Casino Led"
    elif spec_conc >= 0.4: spec_label = "Full Market"
    else: spec_label = "Institutional Bid"
    
    return {
        "RiskLevel": risk_label,
        "Participation": breadth_label,
        "Structure": spec_label
    }

def translate_regime(
    risk: float, 
    breadth: float, 
    spec_conc: float, 
    buckets: Dict[str, Dict[str, float]]
) -> Dict[str, str]:
    """
    Step 2-4: Archetypes and Degree Modifiers.
    """
    
    majors_score = buckets.get("majors", {}).get("wQ", 0.0)
    mid_score = buckets.get("midcaps", {}).get("wQ", 0.0)
    meme_score = buckets.get("memes", {}).get("wQ", 0.0)
    
    primary_label = "Unknown"
    description = ""
    
    # Regime Logic per success.md
    
    # 6. Speculative Divergence (Check first as it handles the specific "Bad Market but Memes" case)
    # Condition: RISK <= 0 (or near 0, doc says "Mildly positive"), SpecConc high, MajorsScore negative
    if (risk <= 0.4) and spec_conc > 0.5 and majors_score < 0:
        primary_label = "Speculative Flight"
        description = "Shit Market, Memes Pumping"

    # 5. Panic / Liquidation Regime
    # Condition: RISK << 0, Meme very negative, Breadth very low
    elif risk < -0.2 and meme_score < -0.1 and breadth < 0.2:
        primary_label = "Liquidation Mode"
        description = "Alts Getting Nuked"

    # 1. Healthy Risk-On
    # Condition: RISK > 0, Breadth high, SpecConc medium or low
    elif risk > 0 and breadth > 0.5 and spec_conc < 0.6:
        primary_label = "Broad Risk-On"
        description = "Rotation Is Real"
        
    # 2. Frothy Risk-On
    # Condition: RISK > 0, SpecConc high, Breadth medium/low
    elif risk > 0 and spec_conc >= 0.6:
        primary_label = "Degenerate Send"
        description = "Memes Running the Market"
        
    # 3. Rotation / Transition
    # Condition: RISK near 0, Mid > Majors, Breadth medium
    elif abs(risk) < 0.05 and mid_score > majors_score and breadth > 0.3:
        primary_label = "Rotation Phase"
        description = "Capital Shifting Under the Hood"
        
    # 4. Structural Risk-Off
    # Condition: RISK < 0, Majors weak, Breadth low
    elif risk < 0 and majors_score < 0 and breadth < 0.4:
         primary_label = "Risk-Off"
         description = "Capital Hiding in BTC"
         
    # Default / Fallback based on Risk Level Intensity
    else:
        if risk > 0:
            primary_label = "Risk On (Scattershot)"
        else:
            primary_label = "Risk Off (Bleeding)"
            
    # Degree Modifier
    modifier = ""
    abs_risk = abs(risk)
    if abs_risk > 0.5: 
        modifier = "Violent"
    elif abs_risk > 0.2:
        modifier = "Heavy"
    elif abs_risk < 0.05:
        modifier = "Light"
        
    # Final String Assembly
    parts = []
    if modifier:
        parts.append(modifier)
    parts.append(primary_label)
    if description:
        parts.append(f"— {description}")
        
    full_string = " ".join(parts)
    
    return {
        "Primary": primary_label,
        "Description": description,
        "Modifier": modifier,
        "Full": full_string
    }
