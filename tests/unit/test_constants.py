"""
Unit tests for Calibration Constants
"""

import unittest
from src.constants import CalibrationConfig


class TestCalibrationConfig(unittest.TestCase):
    """Test cases for CalibrationConfig class"""

    def test_initialization_with_defaults(self):
        """Test dataclass initializes with default values"""
        config = CalibrationConfig()

        self.assertEqual(config.speed_cm_per_sec, 10.0)
        self.assertEqual(config.turn_rate_deg_per_sec, 90.0)
        self.assertEqual(config.cell_size_cm, 30.0)

    def test_initialization_with_custom_values(self):
        """Test dataclass initializes with custom values"""
        config = CalibrationConfig(
            speed_cm_per_sec=15.0,
            turn_rate_deg_per_sec=80.0,
            cell_size_cm=25.0
        )

        self.assertEqual(config.speed_cm_per_sec, 15.0)
        self.assertEqual(config.turn_rate_deg_per_sec, 80.0)
        self.assertEqual(config.cell_size_cm, 25.0)


if __name__ == "__main__":
    unittest.main()
