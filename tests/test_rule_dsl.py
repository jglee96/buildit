import unittest

from app.services.rule_dsl import evaluate_expression


class RuleDslTest(unittest.TestCase):
    def test_lte_passes(self) -> None:
        passed, detail = evaluate_expression({"op": "lte", "field": "far", "value": 500}, {"far": 480})
        self.assertTrue(passed)
        self.assertIn("<= 500", detail)

    def test_between_fails(self) -> None:
        passed, detail = evaluate_expression({"op": "between", "field": "height", "min": 20, "max": 40}, {"height": 50})
        self.assertFalse(passed)
        self.assertIn("<= height=50.00 <=", detail)


if __name__ == "__main__":
    unittest.main()
