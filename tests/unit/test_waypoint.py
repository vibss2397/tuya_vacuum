"""
Unit tests for Waypoint dataclass
"""

import unittest
from src.waypoint import Waypoint


class TestWaypoint(unittest.TestCase):
    """Test cases for Waypoint dataclass"""

    def test_waypoint_creation(self):
        """Test creating a waypoint with all fields"""
        waypoint = Waypoint(
            x_cm=15.5,
            y_cm=42.3,
            orientation="NORTH",
            timestamp=123.45
        )

        self.assertEqual(waypoint.x_cm, 15.5)
        self.assertEqual(waypoint.y_cm, 42.3)
        self.assertEqual(waypoint.orientation, "NORTH")
        self.assertEqual(waypoint.timestamp, 123.45)

    def test_waypoint_without_timestamp(self):
        """Test creating a waypoint without timestamp"""
        waypoint = Waypoint(
            x_cm=10.0,
            y_cm=20.0,
            orientation="EAST"
        )

        self.assertEqual(waypoint.x_cm, 10.0)
        self.assertEqual(waypoint.y_cm, 20.0)
        self.assertEqual(waypoint.orientation, "EAST")
        self.assertIsNone(waypoint.timestamp)

    def test_all_valid_orientations(self):
        """Test all valid orientations"""
        valid_orientations = ["NORTH", "SOUTH", "EAST", "WEST"]

        for orientation in valid_orientations:
            waypoint = Waypoint(x_cm=0.0, y_cm=0.0, orientation=orientation)
            self.assertEqual(waypoint.orientation, orientation)

    def test_invalid_orientation_raises_error(self):
        """Test that invalid orientation raises ValueError"""
        with self.assertRaises(ValueError) as context:
            Waypoint(x_cm=0.0, y_cm=0.0, orientation="INVALID")

        self.assertIn("Invalid orientation", str(context.exception))


if __name__ == "__main__":
    unittest.main()
