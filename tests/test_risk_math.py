import unittest
from risk_regime_bro import risk_engine

class TestRiskEngine(unittest.TestCase):
    
    def setUp(self):
        self.buckets = {
            "majors": ["eth"],
            "memes": ["doge"]
        }
        
    def test_log_return(self):
        # ln(110/100) approx 0.0953
        ret = risk_engine.calculate_log_return(110, 100)
        self.assertAlmostEqual(ret, 0.09531, places=5)
        
    def test_risk_calculation_risk_on(self):
        """
        Scenario: BTC flat, Alts up.
        Expect: Positive Risk Score.
        """
        btc_data = {"current": 100, "prev": 100} # 0% return
        
        market_data = {
            "bitcoin": btc_data,
            "eth": {"current": 105, "prev": 100}, # +5%
            "doge": {"current": 110, "prev": 100} # +10%
        }
        
        # Manually:
        # BTC ret = 0
        # ETH ret = ln(1.05) ~ 0.04879. r_i = 0.04879 - 0 = 0.04879
        # DOGE ret = ln(1.10) ~ 0.09531. r_i = 0.09531 - 0 = 0.09531
        
        # Majors Bucket (ETH): 
        # S = 0.04879
        # B = 1.0 (1/1 > 0)
        # Q = S * (2*1 - 1) = S * 1 = 0.04879
        # wQ = 1 * S = 0.04879
        
        # Memes Bucket (DOGE):
        # S = 0.09531
        # B = 1.0
        # Q = 0.09531
        # wQ = 5 * 0.09531 = 0.47655
        
        # Total Risk = 0.04879 + 0.47655 = 0.52534
        
        results = risk_engine.calculate_risk_metrics(market_data, btc_data, self.buckets)
        
        self.assertAlmostEqual(results['RISK'], 0.52534, places=4)
        self.assertGreater(results['RISK'], 0)
        
    def test_risk_calculation_divergence(self):
        """
        Scenario: BTC flat, Majors down, Memes up.
        Expect: Check if SpecConc is high.
        """
        btc_data = {"current": 100, "prev": 100}
        
        market_data = {
            "bitcoin": btc_data,
            "eth": {"current": 95, "prev": 100}, # -5%
            "doge": {"current": 120, "prev": 100} # +20%
        }
        
        results = risk_engine.calculate_risk_metrics(market_data, btc_data, self.buckets)
        
        # Majors: r_i negative -> Q negative
        # Memes: r_i positive -> Q positive
        
        # SpecConc should be high because Memes are carrying the wQ sum
        self.assertGreater(results['SpecConc'], 0.5)

if __name__ == '__main__':
    unittest.main()
