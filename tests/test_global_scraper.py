import unittest

from global_scraper import next_stable_bottom_rounds


class GlobalScraperScrollTests(unittest.TestCase):
    def test_stability_does_not_advance_before_bottom(self):
        rounds = next_stable_bottom_rounds(
            at_bottom=False,
            count=80,
            height=24000,
            previous_count=80,
            previous_height=24000,
            current_rounds=3,
        )
        self.assertEqual(rounds, 0)

    def test_stability_advances_only_for_same_bottom_state(self):
        rounds = next_stable_bottom_rounds(
            at_bottom=True,
            count=98,
            height=26000,
            previous_count=98,
            previous_height=26000,
            current_rounds=2,
        )
        self.assertEqual(rounds, 3)
        reset = next_stable_bottom_rounds(
            at_bottom=True,
            count=99,
            height=26100,
            previous_count=98,
            previous_height=26000,
            current_rounds=3,
        )
        self.assertEqual(reset, 0)


if __name__ == "__main__":
    unittest.main()
