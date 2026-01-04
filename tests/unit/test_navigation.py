"""
Unit tests for navigation functionality (goto command)
"""

import unittest
from src.brain import Brain
from src.robot import VacuumRobot
from src.room import WorldMap, Room, Point
from src.constants import CalibrationConfig


class TestNavigation(unittest.TestCase):
    """Test cases for navigation along room edges"""

    def setUp(self):
        """Set up a simple rectangular room for testing"""
        config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        robot = VacuumRobot()
        world_map = WorldMap()

        # Create a rectangular room
        # Rectangle: (0,0) -> (60,0) -> (60,90) -> (0,90) -> (0,0)
        polygon = [
            Point(0.0, 0.0),
            Point(60.0, 0.0),
            Point(60.0, 90.0),
            Point(0.0, 90.0)
        ]
        room = Room(name="kitchen", polygons=[polygon])

        # Set edge aliases
        room.set_edge_alias(0, 0, "south")  # (0,0) -> (60,0)
        room.set_edge_alias(0, 1, "east")   # (60,0) -> (60,90)
        room.set_edge_alias(0, 2, "north")  # (60,90) -> (0,90)
        room.set_edge_alias(0, 3, "west")   # (0,90) -> (0,0)

        world_map.add_room(room)
        self.brain = Brain(robot, world_map, config)
        self.room = room

    def test_navigate_adjacent_edges_clockwise(self):
        """Test navigation between adjacent edges (clockwise)"""
        waypoints = self.brain.navigate_to_edge("kitchen", "south", "east")

        # Should have 3 waypoints: start of south, end of south/start of east, end of east
        self.assertEqual(len(waypoints), 3)

        # Check start position (facing east along south edge)
        self.assertEqual(waypoints[0], (0.0, 0.0, "EAST"))

        # Check corner position (after completing south edge, now facing north for east edge)
        self.assertEqual(waypoints[1], (60.0, 0.0, "NORTH"))

        # Check end position (after completing east edge, facing west for next edge)
        self.assertEqual(waypoints[2], (60.0, 90.0, "WEST"))

    def test_navigate_opposite_edges(self):
        """Test navigation between opposite edges"""
        waypoints = self.brain.navigate_to_edge("kitchen", "south", "north")

        # Should go clockwise (shorter path): south -> east -> north
        self.assertEqual(len(waypoints), 4)

        # Verify path
        self.assertEqual(waypoints[0], (0.0, 0.0, "EAST"))    # Start of south edge
        self.assertEqual(waypoints[1], (60.0, 0.0, "NORTH"))   # Corner: end of south, start of east
        self.assertEqual(waypoints[2], (60.0, 90.0, "WEST"))   # Corner: end of east, start of north
        self.assertEqual(waypoints[3], (0.0, 90.0, "SOUTH"))   # End of north edge

    def test_navigate_counter_clockwise(self):
        """Test that the shorter path is chosen (counter-clockwise)"""
        waypoints = self.brain.navigate_to_edge("kitchen", "south", "west")

        # Should go counter-clockwise: south -> west (1 edge)
        # versus clockwise: south -> east -> north -> west (3 edges)
        self.assertEqual(len(waypoints), 2)

        # Start at beginning of south edge
        self.assertEqual(waypoints[0][0], 0.0)
        self.assertEqual(waypoints[0][1], 0.0)

        # End at beginning of west edge (which is same as start of south going backwards)
        self.assertEqual(waypoints[1][0], 0.0)
        self.assertEqual(waypoints[1][1], 90.0)

    def test_navigate_same_edge(self):
        """Test navigation from an edge to itself"""
        waypoints = self.brain.navigate_to_edge("kitchen", "south", "south")

        # Should have just 2 waypoints: start and end of the same edge
        self.assertEqual(len(waypoints), 2)
        self.assertEqual(waypoints[0], (0.0, 0.0, "EAST"))   # Start of south edge
        self.assertEqual(waypoints[1], (60.0, 0.0, "NORTH"))  # End of south edge (orientation for next edge)

    def test_navigate_invalid_room(self):
        """Test navigation with invalid room name"""
        with self.assertRaises(ValueError) as context:
            self.brain.navigate_to_edge("nonexistent", "south", "north")
        self.assertIn("not found", str(context.exception))

    def test_navigate_invalid_start_alias(self):
        """Test navigation with invalid start alias"""
        with self.assertRaises(ValueError) as context:
            self.brain.navigate_to_edge("kitchen", "invalid_alias", "north")
        self.assertIn("not found", str(context.exception))

    def test_navigate_invalid_end_alias(self):
        """Test navigation with invalid end alias"""
        with self.assertRaises(ValueError) as context:
            self.brain.navigate_to_edge("kitchen", "south", "invalid_alias")
        self.assertIn("not found", str(context.exception))

    def test_calculate_orientation_east(self):
        """Test orientation calculation for eastward movement"""
        orientation = self.brain._calculate_orientation(
            Point(0.0, 0.0),
            Point(60.0, 0.0)
        )
        self.assertEqual(orientation, "EAST")

    def test_calculate_orientation_west(self):
        """Test orientation calculation for westward movement"""
        orientation = self.brain._calculate_orientation(
            Point(60.0, 0.0),
            Point(0.0, 0.0)
        )
        self.assertEqual(orientation, "WEST")

    def test_calculate_orientation_north(self):
        """Test orientation calculation for northward movement"""
        orientation = self.brain._calculate_orientation(
            Point(0.0, 0.0),
            Point(0.0, 90.0)
        )
        self.assertEqual(orientation, "NORTH")

    def test_calculate_orientation_south(self):
        """Test orientation calculation for southward movement"""
        orientation = self.brain._calculate_orientation(
            Point(0.0, 90.0),
            Point(0.0, 0.0)
        )
        self.assertEqual(orientation, "SOUTH")

    def test_calculate_orientation_diagonal_raises_error(self):
        """Test that diagonal movement raises an error"""
        with self.assertRaises(ValueError) as context:
            self.brain._calculate_orientation(
                Point(0.0, 0.0),
                Point(60.0, 90.0)
            )
        self.assertIn("not axis-aligned", str(context.exception))


if __name__ == "__main__":
    unittest.main()
