"""
Integration test for complete navigation workflow with auto-assigned aliases
"""

import unittest
from src.brain import Brain
from src.robot import VacuumRobot
from src.room import WorldMap
from src.constants import CalibrationConfig
from src.controller import Controller
from src.persistence import serialize_map, deserialize_map


class TestNavigationWorkflow(unittest.TestCase):
    """End-to-end test for mapping, auto-aliasing, and navigation"""

    def setUp(self):
        """Set up a complete system"""
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.brain = Brain(self.robot, self.world_map, self.config)
        self.controller = Controller(brain=self.brain)

    def test_complete_workflow_with_auto_aliases(self):
        """Test complete workflow: map -> save (auto-alias) -> navigate"""

        # 1. Start mapping using controller
        parsed = self.controller.parse_command(":start kitchen 0 0 NORTH")
        result = self.controller.execute_command(parsed)
        self.assertIn("Started mapping", result)

        # 2. Trace a room using keyboard simulation
        self.controller.handle_key_press("UP")
        self.controller.handle_key_release("UP")  # This records movement with duration
        # Simulate actual movement by directly recording
        self.brain.record_movement(3.0)  # 30cm north

        self.controller.handle_key_press("RIGHT")
        self.brain.record_movement(6.0)  # 60cm east

        self.controller.handle_key_press("RIGHT")
        self.brain.record_movement(3.0)  # 30cm south

        self.controller.handle_key_press("RIGHT")
        self.brain.record_movement(6.0)  # 60cm west (back to start)

        # 3. Save the room (should auto-assign aliases)
        parsed = self.controller.parse_command(":save")
        result = self.controller.execute_command(parsed)
        self.assertIn("saved", result)

        # 4. Verify auto-assigned aliases exist
        room = self.world_map.get_room("kitchen")
        self.assertIsNotNone(room)
        self.assertGreater(len(room.edge_aliases), 0)

        # Verify aliases follow the pattern edge_0_0, edge_0_1, etc.
        for edge_idx in range(len(room.polygons[0])):
            alias = room.get_edge_alias(0, edge_idx)
            self.assertEqual(alias, f"edge_0_{edge_idx}")

        # 5. Use goto command with auto-assigned aliases
        parsed = self.controller.parse_command(":goto kitchen edge_0_0 edge_0_2")
        result = self.controller.execute_command(parsed)
        self.assertIn("Navigation path", result)
        self.assertIn("edge_0_0", result)
        self.assertIn("edge_0_2", result)

    def test_persistence_preserves_auto_aliases(self):
        """Test that auto-assigned aliases are saved and restored"""

        # 1. Map and save a room (auto-assigns aliases)
        self.brain.start_mapping("living_room", 0.0, 0.0, "NORTH")
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(5.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(5.0)
        self.brain.save_room()

        # 2. Serialize the map
        json_string = serialize_map(self.world_map, self.config)

        # 3. Deserialize into a new map
        restored_map, restored_config = deserialize_map(json_string)

        # 4. Verify auto-assigned aliases were preserved
        restored_room = restored_map.get_room("living_room")
        self.assertIsNotNone(restored_room)

        # Check that all aliases were restored
        num_edges = len(restored_room.polygons[0])
        self.assertEqual(len(restored_room.edge_aliases), num_edges)

        for edge_idx in range(num_edges):
            expected_alias = f"edge_0_{edge_idx}"
            actual_alias = restored_room.get_edge_alias(0, edge_idx)
            self.assertEqual(actual_alias, expected_alias)

    def test_multiple_rooms_with_auto_aliases(self):
        """Test that each room gets its own set of auto-assigned aliases"""

        # Map first room
        self.brain.start_mapping("room1", 0.0, 0.0, "NORTH")
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.save_room()

        # Map second room (starting from a point in room1)
        room1 = self.world_map.get_room("room1")
        start_point = room1.polygons[0][0]

        self.brain.start_mapping("room2", start_point.x_cm, start_point.y_cm, "EAST")
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(4.0)
        self.brain.save_room()

        # Verify both rooms have independent aliases
        room1 = self.world_map.get_room("room1")
        room2 = self.world_map.get_room("room2")

        # Both should have edge_0_0, edge_0_1, etc.
        self.assertEqual(room1.get_edge_alias(0, 0), "edge_0_0")
        self.assertEqual(room2.get_edge_alias(0, 0), "edge_0_0")

        # Verify we can navigate in each room independently
        waypoints1 = self.brain.navigate_to_edge("room1", "edge_0_0", "edge_0_1")
        waypoints2 = self.brain.navigate_to_edge("room2", "edge_0_0", "edge_0_1")

        self.assertGreater(len(waypoints1), 0)
        self.assertGreater(len(waypoints2), 0)

    def test_manual_alias_override_still_works(self):
        """Test that :alias command can override auto-assigned aliases"""

        # Map and save room (auto-assigns aliases)
        self.brain.start_mapping("bedroom", 0.0, 0.0, "NORTH")
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)
        self.brain.save_room()

        # Verify auto-alias exists
        room = self.world_map.get_room("bedroom")
        self.assertEqual(room.get_edge_alias(0, 0), "edge_0_0")

        # Override with custom alias using :alias command
        parsed = self.controller.parse_command(":alias bedroom 0 0 south_wall")
        result = self.controller.execute_command(parsed)
        self.assertIn("Assigned alias 'south_wall'", result)

        # Verify override worked
        self.assertEqual(room.get_edge_alias(0, 0), "south_wall")

        # Verify navigation works with custom alias
        parsed = self.controller.parse_command(":goto bedroom south_wall edge_0_1")
        result = self.controller.execute_command(parsed)
        self.assertIn("Navigation path", result)


if __name__ == "__main__":
    unittest.main()
