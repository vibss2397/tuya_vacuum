"""
Unit tests for Virtual Robot
"""

import unittest
from src.robot import VacuumRobot


class TestVacuumRobot(unittest.TestCase):
    """Test cases for VacuumRobot class"""

    def test_robot_initialization(self):
        """Test robot initializes at correct position with given orientation"""
        robot = VacuumRobot(x=5, y=10, orientation="EAST")

        self.assertEqual(robot.get_position(), (5, 10))
        self.assertEqual(robot.get_orientation(), "EAST")

    def test_robot_default_initialization(self):
        """Test robot initializes at origin facing NORTH by default"""
        robot = VacuumRobot()

        self.assertEqual(robot.get_position(), (0, 0))
        self.assertEqual(robot.get_orientation(), "NORTH")

    def test_position_setters_and_getters(self):
        """Test setting and getting position works correctly"""
        robot = VacuumRobot()

        robot.set_position(3, 7)
        self.assertEqual(robot.get_position(), (3, 7))

        robot.set_position(-2, 5)
        self.assertEqual(robot.get_position(), (-2, 5))

    def test_orientation_setters_and_getters(self):
        """Test setting and getting orientation works correctly"""
        robot = VacuumRobot()

        robot.set_orientation("SOUTH")
        self.assertEqual(robot.get_orientation(), "SOUTH")

        robot.set_orientation("WEST")
        self.assertEqual(robot.get_orientation(), "WEST")

    def test_invalid_orientation_raises_error(self):
        """Test that invalid orientation raises ValueError"""
        robot = VacuumRobot()

        with self.assertRaises(ValueError):
            robot.set_orientation("NORTHEAST")


if __name__ == "__main__":
    unittest.main()
