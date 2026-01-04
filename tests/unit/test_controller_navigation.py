"""
Unit tests for Controller navigation commands (goto and alias)
"""

import unittest
from src.controller import Controller
from src.brain import Brain
from src.robot import VacuumRobot
from src.room import WorldMap, Room, Point
from src.constants import CalibrationConfig


class TestControllerNavigationCommands(unittest.TestCase):
    """Test cases for navigation-related controller commands"""

    def setUp(self):
        """Set up controller with a simple room"""
        config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        robot = VacuumRobot()
        world_map = WorldMap()

        # Create a rectangular room
        polygon = [
            Point(0.0, 0.0),
            Point(60.0, 0.0),
            Point(60.0, 90.0),
            Point(0.0, 90.0)
        ]
        room = Room(name="kitchen", polygons=[polygon])
        world_map.add_room(room)

        brain = Brain(robot, world_map, config)
        self.controller = Controller(brain=brain)
        self.brain = brain

    def test_parse_alias_command(self):
        """Test parsing :alias command"""
        parsed = self.controller.parse_command(":alias kitchen 0 1 east_wall")

        self.assertEqual(parsed.command, "alias")
        self.assertEqual(parsed.params["room_name"], "kitchen")
        self.assertEqual(parsed.params["polygon_idx"], 0)
        self.assertEqual(parsed.params["edge_idx"], 1)
        self.assertEqual(parsed.params["alias"], "east_wall")

    def test_parse_alias_command_invalid_syntax(self):
        """Test parsing :alias command with invalid syntax"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":alias kitchen 0")
        self.assertIn("Invalid :alias syntax", str(context.exception))

    def test_parse_alias_command_invalid_indices(self):
        """Test parsing :alias command with non-integer indices"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":alias kitchen abc 1 wall")
        self.assertIn("must be integers", str(context.exception))

    def test_parse_goto_command(self):
        """Test parsing :goto command"""
        parsed = self.controller.parse_command(":goto kitchen south north")

        self.assertEqual(parsed.command, "goto")
        self.assertEqual(parsed.params["room_name"], "kitchen")
        self.assertEqual(parsed.params["start_alias"], "south")
        self.assertEqual(parsed.params["end_alias"], "north")

    def test_parse_goto_command_invalid_syntax(self):
        """Test parsing :goto command with invalid syntax"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":goto kitchen south")
        self.assertIn("Invalid :goto syntax", str(context.exception))

    def test_execute_alias_command(self):
        """Test executing :alias command"""
        parsed = self.controller.parse_command(":alias kitchen 0 1 east_wall")
        result = self.controller.execute_command(parsed)

        self.assertIn("Assigned alias 'east_wall'", result)
        self.assertIn("kitchen", result)

        # Verify alias was set
        room = self.brain.world_map.get_room("kitchen")
        self.assertEqual(room.get_edge_alias(0, 1), "east_wall")

    def test_execute_alias_command_invalid_room(self):
        """Test executing :alias command with invalid room"""
        parsed = self.controller.parse_command(":alias nonexistent 0 1 wall")

        with self.assertRaises(ValueError) as context:
            self.controller.execute_command(parsed)
        self.assertIn("not found", str(context.exception))

    def test_execute_goto_command(self):
        """Test executing :goto command"""
        # First, set up aliases
        room = self.brain.world_map.get_room("kitchen")
        room.set_edge_alias(0, 0, "south")
        room.set_edge_alias(0, 2, "north")

        # Execute goto command
        parsed = self.controller.parse_command(":goto kitchen south north")
        result = self.controller.execute_command(parsed)

        self.assertIn("Navigation path", result)
        self.assertIn("south", result)
        self.assertIn("north", result)
        self.assertIn("waypoints", result)

    def test_execute_goto_command_invalid_room(self):
        """Test executing :goto command with invalid room"""
        parsed = self.controller.parse_command(":goto nonexistent south north")

        with self.assertRaises(ValueError) as context:
            self.controller.execute_command(parsed)
        self.assertIn("not found", str(context.exception))

    def test_execute_goto_command_invalid_alias(self):
        """Test executing :goto command with invalid alias"""
        room = self.brain.world_map.get_room("kitchen")
        room.set_edge_alias(0, 0, "south")

        parsed = self.controller.parse_command(":goto kitchen south invalid")

        with self.assertRaises(ValueError) as context:
            self.controller.execute_command(parsed)
        self.assertIn("not found", str(context.exception))

    def test_full_workflow_with_aliases_and_goto(self):
        """Test full workflow: map room, assign aliases, navigate"""
        # Set up aliases
        room = self.brain.world_map.get_room("kitchen")
        room.set_edge_alias(0, 0, "south")
        room.set_edge_alias(0, 1, "east")
        room.set_edge_alias(0, 2, "north")
        room.set_edge_alias(0, 3, "west")

        # Test each goto combination
        test_cases = [
            ("south", "east"),
            ("east", "north"),
            ("north", "west"),
            ("west", "south"),
        ]

        for start, end in test_cases:
            parsed = self.controller.parse_command(f":goto kitchen {start} {end}")
            result = self.controller.execute_command(parsed)
            self.assertIn("Navigation path", result)
            self.assertIn(start, result)
            self.assertIn(end, result)


if __name__ == "__main__":
    unittest.main()
