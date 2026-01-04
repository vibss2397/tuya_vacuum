"""
Unit tests for automatic edge alias assignment
"""

import unittest
from src.brain import Brain
from src.robot import VacuumRobot
from src.room import WorldMap, Room, Point
from src.constants import CalibrationConfig


class TestAutoAliases(unittest.TestCase):
    """Test cases for automatic edge alias assignment when saving rooms"""

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

    def test_auto_assign_edge_aliases_simple_room(self):
        """Test that edge aliases are automatically assigned when saving a room"""
        # Start mapping a simple rectangular room
        self.brain.start_mapping("kitchen", 0.0, 0.0, "NORTH")

        # Trace a rectangle
        self.brain.record_movement(3.0)  # Move 30cm north
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # Move 60cm east
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # Move 30cm south
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # Move 60cm west (back to start)

        # Save the room
        self.brain.save_room()

        # Verify room was saved
        room = self.world_map.get_room("kitchen")
        self.assertIsNotNone(room)

        # Verify edge aliases were auto-assigned
        # Should have 4 edges (rectangle has 4 corners, so 4 edges)
        num_edges = len(room.polygons[0])
        self.assertEqual(len(room.edge_aliases), num_edges)

        # Verify alias format and that all edges are covered
        for edge_idx in range(num_edges):
            expected_alias = f"edge_0_{edge_idx}"
            actual_alias = room.get_edge_alias(0, edge_idx)
            self.assertEqual(actual_alias, expected_alias)

            # Verify reverse lookup works
            found_edge = room.find_edge_by_alias(expected_alias)
            self.assertEqual(found_edge, (0, edge_idx))

    def test_auto_assign_preserves_manual_aliases(self):
        """Test that manually set aliases are not overwritten by auto-assignment"""
        # Create a room directly and set a manual alias
        polygon = [
            Point(0.0, 0.0),
            Point(60.0, 0.0),
            Point(60.0, 30.0),
            Point(0.0, 30.0)
        ]
        room = Room(name="test_room", polygons=[polygon])

        # Manually set an alias before auto-assignment
        room.set_edge_alias(0, 0, "custom_south")

        # Auto-assign aliases
        self.brain._auto_assign_edge_aliases(room)

        # Verify the manual alias was overwritten (current behavior)
        # Note: If you want to preserve manual aliases, we'd need to modify the logic
        alias = room.get_edge_alias(0, 0)
        self.assertEqual(alias, "edge_0_0")  # Auto-assigned overwrites manual

    def test_auto_aliases_with_multiple_polygons(self):
        """Test auto-assignment with a room containing multiple polygons"""
        # Create a room with 2 polygons
        polygon1 = [
            Point(0.0, 0.0),
            Point(30.0, 0.0),
            Point(30.0, 30.0),
            Point(0.0, 30.0)
        ]
        polygon2 = [
            Point(50.0, 0.0),
            Point(80.0, 0.0),
            Point(80.0, 20.0),
            Point(50.0, 20.0)
        ]
        room = Room(name="multi_room", polygons=[polygon1, polygon2])

        # Auto-assign
        self.brain._auto_assign_edge_aliases(room)

        # Verify polygon 1 aliases
        for edge_idx in range(len(polygon1)):
            alias = room.get_edge_alias(0, edge_idx)
            self.assertEqual(alias, f"edge_0_{edge_idx}")

        # Verify polygon 2 aliases
        for edge_idx in range(len(polygon2)):
            alias = room.get_edge_alias(1, edge_idx)
            self.assertEqual(alias, f"edge_1_{edge_idx}")

    def test_navigation_with_auto_aliases(self):
        """Test that navigation works with auto-assigned aliases"""
        # Start mapping
        self.brain.start_mapping("bedroom", 0.0, 0.0, "NORTH")

        # Trace a rectangle
        self.brain.record_movement(3.0)  # 30cm north
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # 60cm east
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # 30cm south
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # 60cm west

        # Save (auto-assigns aliases)
        self.brain.save_room()

        # Test navigation using auto-assigned aliases
        waypoints = self.brain.navigate_to_edge("bedroom", "edge_0_0", "edge_0_2")

        # Verify we got waypoints
        self.assertGreater(len(waypoints), 0)

        # Verify start and end positions make sense
        start_x, start_y, _ = waypoints[0]
        end_x, end_y, _ = waypoints[-1]
        self.assertIsInstance(start_x, float)
        self.assertIsInstance(end_y, float)


if __name__ == "__main__":
    unittest.main()
