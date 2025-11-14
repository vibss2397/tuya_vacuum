"""
Unit tests for Virtual Robot
"""

import unittest
from src.robot import VirtualRobot


class TestVirtualRobot(unittest.TestCase):
    """Test cases for VirtualRobot class"""

    def test_robot_initialization(self):
        """Test robot initializes at correct position with given orientation"""
        robot = VirtualRobot(x=5, y=10, orientation="EAST")

        self.assertEqual(robot.get_position(), (5, 10))
        self.assertEqual(robot.get_orientation(), "EAST")

    def test_robot_default_initialization(self):
        """Test robot initializes at origin facing NORTH by default"""
        robot = VirtualRobot()

        self.assertEqual(robot.get_position(), (0, 0))
        self.assertEqual(robot.get_orientation(), "NORTH")

    def test_position_setters_and_getters(self):
        """Test setting and getting position works correctly"""
        robot = VirtualRobot()

        robot.set_position(3, 7)
        self.assertEqual(robot.get_position(), (3, 7))

        robot.set_position(-2, 5)
        self.assertEqual(robot.get_position(), (-2, 5))

    def test_orientation_setters_and_getters(self):
        """Test setting and getting orientation works correctly"""
        robot = VirtualRobot()

        robot.set_orientation("SOUTH")
        self.assertEqual(robot.get_orientation(), "SOUTH")

        robot.set_orientation("WEST")
        self.assertEqual(robot.get_orientation(), "WEST")

    def test_invalid_orientation_raises_error(self):
        """Test that invalid orientation raises ValueError"""
        robot = VirtualRobot()

        with self.assertRaises(ValueError):
            robot.set_orientation("NORTHEAST")


if __name__ == "__main__":
    unittest.main()
