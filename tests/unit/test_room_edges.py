"""
Unit tests for Room edge alias functionality
"""

import unittest
from src.room import Room, Point


class TestRoomEdgeAliases(unittest.TestCase):
    """Test cases for Room edge alias functionality"""

    def setUp(self):
        """Set up a simple rectangular room for testing"""
        # Rectangle: (0,0) -> (60,0) -> (60,90) -> (0,90) -> (0,0)
        self.polygon = [
            Point(0.0, 0.0),
            Point(60.0, 0.0),
            Point(60.0, 90.0),
            Point(0.0, 90.0)
        ]
        self.room = Room(name="test_room", polygons=[self.polygon])

    def test_set_edge_alias(self):
        """Test setting an edge alias"""
        self.room.set_edge_alias(0, 0, "south_wall")
        alias = self.room.get_edge_alias(0, 0)
        self.assertEqual(alias, "south_wall")

    def test_get_edge_alias_nonexistent(self):
        """Test getting an alias that doesn't exist"""
        alias = self.room.get_edge_alias(0, 0)
        self.assertIsNone(alias)

    def test_set_multiple_aliases(self):
        """Test setting multiple edge aliases"""
        self.room.set_edge_alias(0, 0, "south_wall")
        self.room.set_edge_alias(0, 1, "east_wall")
        self.room.set_edge_alias(0, 2, "north_wall")
        self.room.set_edge_alias(0, 3, "west_wall")

        self.assertEqual(self.room.get_edge_alias(0, 0), "south_wall")
        self.assertEqual(self.room.get_edge_alias(0, 1), "east_wall")
        self.assertEqual(self.room.get_edge_alias(0, 2), "north_wall")
        self.assertEqual(self.room.get_edge_alias(0, 3), "west_wall")

    def test_overwrite_alias(self):
        """Test overwriting an existing alias"""
        self.room.set_edge_alias(0, 0, "old_alias")
        self.assertEqual(self.room.get_edge_alias(0, 0), "old_alias")

        self.room.set_edge_alias(0, 0, "new_alias")
        self.assertEqual(self.room.get_edge_alias(0, 0), "new_alias")

    def test_find_edge_by_alias(self):
        """Test finding an edge by its alias"""
        self.room.set_edge_alias(0, 2, "north_wall")
        result = self.room.find_edge_by_alias("north_wall")
        self.assertEqual(result, (0, 2))

    def test_find_edge_by_alias_not_found(self):
        """Test finding an alias that doesn't exist"""
        result = self.room.find_edge_by_alias("nonexistent")
        self.assertIsNone(result)

    def test_get_edge_points(self):
        """Test getting the two points that define an edge"""
        start, end = self.room.get_edge_points(0, 0)
        self.assertEqual(start.x_cm, 0.0)
        self.assertEqual(start.y_cm, 0.0)
        self.assertEqual(end.x_cm, 60.0)
        self.assertEqual(end.y_cm, 0.0)

    def test_get_edge_points_wraps_around(self):
        """Test that edge indices wrap around at the end of polygon"""
        # Last edge should connect last point back to first point
        start, end = self.room.get_edge_points(0, 3)
        self.assertEqual(start.x_cm, 0.0)
        self.assertEqual(start.y_cm, 90.0)
        self.assertEqual(end.x_cm, 0.0)
        self.assertEqual(end.y_cm, 0.0)

    def test_set_edge_alias_invalid_polygon_idx(self):
        """Test that invalid polygon index raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.room.set_edge_alias(5, 0, "alias")
        self.assertIn("Invalid polygon_idx", str(context.exception))

    def test_set_edge_alias_invalid_edge_idx(self):
        """Test that invalid edge index raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.room.set_edge_alias(0, 10, "alias")
        self.assertIn("Invalid edge_idx", str(context.exception))

    def test_get_edge_points_invalid_polygon_idx(self):
        """Test that invalid polygon index raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.room.get_edge_points(5, 0)
        self.assertIn("Invalid polygon_idx", str(context.exception))

    def test_get_edge_points_invalid_edge_idx(self):
        """Test that invalid edge index raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.room.get_edge_points(0, 10)
        self.assertIn("Invalid edge_idx", str(context.exception))

    def test_multiple_polygons(self):
        """Test edge aliases with multiple polygons"""
        # Add a second polygon
        polygon2 = [
            Point(100.0, 0.0),
            Point(150.0, 0.0),
            Point(150.0, 50.0),
            Point(100.0, 50.0)
        ]
        room = Room(name="multi_room", polygons=[self.polygon, polygon2])

        # Set aliases on both polygons
        room.set_edge_alias(0, 0, "room1_south")
        room.set_edge_alias(1, 0, "room2_south")

        self.assertEqual(room.get_edge_alias(0, 0), "room1_south")
        self.assertEqual(room.get_edge_alias(1, 0), "room2_south")

        self.assertEqual(room.find_edge_by_alias("room1_south"), (0, 0))
        self.assertEqual(room.find_edge_by_alias("room2_south"), (1, 0))


if __name__ == "__main__":
    unittest.main()
