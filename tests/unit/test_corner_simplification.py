"""
Unit tests for corner simplification logic
"""

import unittest
from src.brain import Brain
from src.robot import VacuumRobot
from src.room import WorldMap, Point
from src.constants import CalibrationConfig


class TestCornerSimplification(unittest.TestCase):
    """Test cases for path simplification to corner points"""

    def setUp(self):
        """Set up a brain for testing"""
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.brain = Brain(self.robot, self.world_map, self.config)

    def test_rectangle_has_exactly_four_corners(self):
        """Test that a traced rectangle simplifies to exactly 4 corners"""
        # Map a rectangle
        self.brain.start_mapping("rect", 0.0, 0.0, "NORTH")
        self.brain.record_movement(3.0)  # 30cm north
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # 60cm east
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # 30cm south
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # 60cm west
        self.brain.save_room()

        # Verify exactly 4 corners
        room = self.world_map.get_room("rect")
        self.assertEqual(len(room.polygons[0]), 4)

        # Verify corners are at expected positions (rectangle)
        corners = room.polygons[0]
        self.assertEqual(corners[0].x_cm, 0.0)
        self.assertEqual(corners[0].y_cm, 0.0)
        self.assertEqual(corners[1].x_cm, 0.0)
        self.assertEqual(corners[1].y_cm, 30.0)
        self.assertEqual(corners[2].x_cm, 60.0)
        self.assertEqual(corners[2].y_cm, 30.0)
        self.assertEqual(corners[3].x_cm, 60.0)
        self.assertEqual(corners[3].y_cm, 0.0)

    def test_no_duplicate_corner_points(self):
        """Test that duplicate points at same location are not created"""
        self.brain.start_mapping("square", 0.0, 0.0, "NORTH")
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.save_room()

        room = self.world_map.get_room("square")
        corners = room.polygons[0]

        # Check no duplicates exist
        positions = [(p.x_cm, p.y_cm) for p in corners]
        unique_positions = set(positions)
        self.assertEqual(len(positions), len(unique_positions),
                        f"Found duplicate corners: {positions}")

    def test_direct_simplification_with_sample_path(self):
        """Test the simplification method directly with a known path"""
        # Create a path that represents moving and turning
        path = [
            (0.0, 0.0, "NORTH"),     # Start
            (0.0, 30.0, "NORTH"),    # After moving north
            (0.0, 30.0, "EAST"),     # Turn right (same position, new orientation)
            (60.0, 30.0, "EAST"),    # After moving east
            (60.0, 30.0, "SOUTH"),   # Turn right
            (60.0, 0.0, "SOUTH"),    # After moving south
            (60.0, 0.0, "WEST"),     # Turn right
            (0.0, 0.0, "WEST"),      # Back to start
        ]

        corners = self.brain._simplify_path_to_corners_cm(path)

        # Should have exactly 4 corners
        self.assertEqual(len(corners), 4)

        # Verify corner positions
        expected_corners = [
            (0.0, 0.0),   # Start
            (0.0, 30.0),  # After north, turn to east
            (60.0, 30.0), # After east, turn to south
            (60.0, 0.0),  # After south, turn to west
        ]

        for i, (expected_x, expected_y) in enumerate(expected_corners):
            self.assertAlmostEqual(corners[i].x_cm, expected_x, places=5)
            self.assertAlmostEqual(corners[i].y_cm, expected_y, places=5)

    def test_l_shape_has_six_corners(self):
        """Test that an L-shape has the correct number of corners"""
        # Map an L-shape (6 corners)
        self.brain.start_mapping("l_shape", 0.0, 0.0, "NORTH")
        self.brain.record_movement(6.0)  # 60cm north
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # 30cm east
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # 30cm south
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # 30cm west (should be back above start)
        self.brain.robot.turn_left()
        self.brain.record_movement(3.0)  # 30cm south
        self.brain.robot.turn_right()
        self.brain.record_movement(0.0001)  # Tiny movement to close (should be at start)

        path = self.brain.get_current_path()
        corners = self.brain._simplify_path_to_corners_cm(path)

        # L-shape should have 6 corners
        self.assertEqual(len(corners), 6)


if __name__ == "__main__":
    unittest.main()
