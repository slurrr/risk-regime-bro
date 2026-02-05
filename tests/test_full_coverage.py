import unittest
from risk_regime_bro import risk_engine

class TestFullCoverage(unittest.TestCase):
    
    def setUp(self):
        # Spec Buckets
        self.buckets = {
            "majors": ["eth"],
            "large_alts": ["ada"],
            "midcaps": ["sui"],
            "high_beta": ["pepe"],
            "memes": ["doge"]
        }
        # Baseline BTC
        self.btc_flat = {"current": 100, "prev": 100}
        
    def _run_engine(self, market_updates):
        """Helper to run engine with shorthand updates."""
        market_data = {"bitcoin": self.btc_flat}
        for sym, (curr, prev) in market_updates.items():
            market_data[sym] = {"current": curr, "prev": prev}
            
        return risk_engine.calculate_risk_metrics(market_data, self.btc_flat, self.buckets)

    def test_math_fix_negative_strength(self):
        """
        Verify that negative strength (underperformance) yields negative risk,
        even with 0 breadth.
        Old Bug: Neg Strength * (2*0 - 1) = Positive.
        """
        # ETH down 10% vs BTC flat
        updates = {
            "eth": (90, 100) # -10%
        }
        res = self._run_engine(updates)
        
        # S_b should be approx -0.105 (ln(0.9))
        # Q_b should be negative (preserved sign)
        # RISK should be negative
        self.assertLess(res['RISK'], 0)
        self.assertEqual(res['Buckets']['majors']['Q_b'], res['Buckets']['majors']['S_b'])

    def test_regime_broad_risk_on(self):
        """RISK > 0, Broad Breadth, Low SpecConc"""
        updates = {
            "eth": (102, 100),  # +2%
            "ada": (102, 100),
            "sui": (102, 100),
            "pepe": (102, 100),
            "doge": (102, 100)
        }
        res = self._run_engine(updates)
        self.assertIn("Broad Risk-On", res['Regime']['Primary'])
        self.assertIn("Institutional Bid", res['Intensities']['Structure'])

    def test_regime_degenerate_send(self):
        """RISK > 0, High SpecConc (Memes leading)"""
        updates = {
            "eth": (101, 100),   # +1%
            # Memes doing heavy lifting for SpecConc (Numerator is Memes only)
            "doge": (120, 100)   # +20% (w=5 -> huge contribution)
        }
        res = self._run_engine(updates)
        self.assertIn("Degenerate Send", res['Regime']['Primary'])
        self.assertIn("Casino Led", res['Intensities']['Structure'])

    def test_regime_rotation_phase(self):
        """
        RISK ~ 0 (<0.05), Mid > Majors. Breadth > 0.3.
        """
        updates = {
            "eth": (100, 100),   # Flat
            "ada": (100.2, 100), # +0.2% (Small boost for breadth > 0.3)
            "sui": (100.5, 100), # +0.5% (Midcap lead)
            "pepe": (100, 100),
            "doge": (100, 100)
        }
        res = self._run_engine(updates)
        # Breadth: 2/5 = 0.4 (> 0.3).
        self.assertIn("Rotation Phase", res['Regime']['Primary'])

    def test_regime_speculative_flight(self):
        """
        Majors DOWN, Memes UP. Risk < 0.4. SpecConc > 0.5.
        """
        updates_valid = {
            "eth": (90, 100),
            "doge": (104, 100) 
        }
        res = self._run_engine(updates_valid)
        self.assertIn("Speculative Flight", res['Regime']['Primary'])
        self.assertIn("Shit Market, Memes Pumping", res['Regime']['Description'])

    def test_regime_liquidation_mode(self):
        """Everything nuking hard."""
        updates = {
            "eth": (80, 100), # -20%
            "ada": (80, 100),
            "sui": (80, 100),
            "pepe": (80, 100),
            "doge": (70, 100) # Memes getting crushed
        }
        res = self._run_engine(updates)
        self.assertIn("Liquidation Mode", res['Regime']['Primary'])
        self.assertIn("Violent", res['Regime']['Modifier']) 

    def test_modifiers(self):
        """Test Light/Heavy/Violent thresholds."""
        # 1. Light Risk Off (< 0.05 abs)
        updates = {"eth": (99.5, 100)} # -0.5% -> -0.005. Fits < 0.05.
        res = self._run_engine(updates)
        self.assertIn("Light", res['Regime']['Modifier'])
        
        # 2. Heavy Risk Off (> 0.2 abs)
        # Use simple single symbol for clarity.
        # W(Doge) = 5. Q = -0.05 (-5%). Total = -0.25 (Abs=0.25) -> Heavy.
        updates_heavy = {"doge": (95, 100)} 
        res_heavy = self._run_engine(updates_heavy)
        self.assertIn("Heavy", res_heavy['Regime']['Modifier'])
        
        # 3. Violent (> 0.5 abs)
        # Doge -15%. Q=-0.15. W=5. Total=-0.75. -> Violent.
        updates_violent = {"doge": (85, 100)}
        res_violent = self._run_engine(updates_violent)
        self.assertIn("Violent", res_violent['Regime']['Modifier'])

    def test_fallback_labels(self):
        """Test 'Bleeding' label logic."""
        # Just a general unstructured downtrend that doesn't fit Liquidation Mode criteria perfectly
        # e.g. Moderate downtrend
        updates = {
            "eth": (95, 100),
            "ada": (95, 100),
            "sui": (95, 100), 
            "pepe": (95, 100),
            "doge": (95, 100)
        }
        res = self._run_engine(updates)
        # Should likely be 'Risk Off' (Structural) or fall back to 'Bleeding' if criteria miss
        # Structural Risk Off conditions: Risk < 0, Majors < 0, Breadth < 0.4.
        # This setup has Breadth=0, Majors<0, Risk<0. So it hits Structural Risk Off.
        
        # To hit "Bleeding" (Fallback), we need to miss the specific archetypes.
        # Maybe Mixed breadth but net negative risk?
        # e.g. Majors UP, Memes DOWN HUGE.
        updates_mixed = {
            "eth": (102, 100), # Majors Up
            "doge": (80, 100)  # Memes Nuke -> Net Negative Risk
        }
        res_mixed = self._run_engine(updates_mixed)
        # MajorsScore > 0 -> Misses Structural Risk Off
        # Risk < 0 -> Hits negative check
        # Should be Risk Off (Bleeding)
        self.assertIn("Risk Off (Bleeding)", res_mixed['Regime']['Primary'])

if __name__ == '__main__':
    unittest.main()
