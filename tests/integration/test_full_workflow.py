"""
Integration tests for complete application workflows
"""

import unittest
import time
import os
import tempfile
from src.robot import VacuumRobot
from src.cell import WorldMap
from src.constants import CalibrationConfig
from src.brain import Brain
from src.controller import Controller, Mode
from src.persistence import save_to_file, load_from_file


class TestFullMappingWorkflow(unittest.TestCase):
    """Test complete mapping workflows end-to-end"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = CalibrationConfig(speed_cm_per_sec=10.0, cell_size_cm=30.0)
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.brain = Brain(self.robot, self.world_map, self.config)
        self.controller = Controller(self.brain)

    def test_map_single_room_workflow(self):
        """Test complete workflow: start -> map -> save"""
        # Start mapping kitchen
        result = self.controller.execute_command(
            self.controller.parse_command(":start kitchen 0 0 NORTH")
        )
        self.assertIn("kitchen", result)
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

        # Map a 2x2 square
        # North 2 cells
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Turn right, move east 2 cells
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Turn right, move south 2 cells
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Turn right, move west 2 cells (back to start)
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Save the room
        self.controller.enter_command_mode()
        result = self.controller.execute_command(
            self.controller.parse_command(":save")
        )

        # Verify
        self.assertIn("saved", result)
        self.assertIn("kitchen", result)
        self.assertIn("kitchen", self.world_map.get_room_names())
        kitchen_cells = self.world_map.get_all_cells_for_room("kitchen")
        self.assertGreater(len(kitchen_cells), 0)

    def test_map_multiple_rooms_workflow(self):
        """Test mapping multiple connected rooms"""
        # Map first room
        self.controller.execute_command(
            self.controller.parse_command(":start living_room 0 0 NORTH")
        )

        # Simple 1x1 square
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Save first room
        self.controller.enter_command_mode()
        self.controller.execute_command(self.controller.parse_command(":save"))

        # Start second room from a cell in first room
        self.controller.execute_command(
            self.controller.parse_command(":start bedroom 0 1 NORTH")
        )

        # Map another square
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Save second room
        self.controller.enter_command_mode()
        self.controller.execute_command(self.controller.parse_command(":save"))

        # Verify both rooms exist
        rooms = self.world_map.get_room_names()
        self.assertEqual(len(rooms), 2)
        self.assertIn("living_room", rooms)
        self.assertIn("bedroom", rooms)

    def test_save_and_load_workflow(self):
        """Test saving map to file and loading it back"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            # Map a room
            self.controller.execute_command(
                self.controller.parse_command(":start office 0 0 NORTH")
            )

            # Simple square
            self.controller.handle_key_press("UP")
            time.sleep(3.0)
            self.controller.handle_key_release("UP")
            self.controller.handle_key_press("RIGHT")
            self.controller.handle_key_press("UP")
            time.sleep(3.0)
            self.controller.handle_key_release("UP")
            self.controller.handle_key_press("RIGHT")
            self.controller.handle_key_press("UP")
            time.sleep(3.0)
            self.controller.handle_key_release("UP")
            self.controller.handle_key_press("RIGHT")
            self.controller.handle_key_press("UP")
            time.sleep(3.0)
            self.controller.handle_key_release("UP")

            self.controller.enter_command_mode()
            self.controller.execute_command(self.controller.parse_command(":save"))

            # Save to file
            save_to_file(self.world_map, self.config, temp_file)

            # Load from file
            loaded_map, loaded_config = load_from_file(temp_file)

            # Verify loaded data matches
            self.assertIn("office", loaded_map.get_room_names())
            original_cells = len(self.world_map.get_all_cells_for_room("office"))
            loaded_cells = len(loaded_map.get_all_cells_for_room("office"))
            self.assertEqual(original_cells, loaded_cells)

        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_resume_command_workflow(self):
        """Test pausing and resuming mapping"""
        # Start mapping
        self.controller.execute_command(
            self.controller.parse_command(":start garage 0 0 NORTH")
        )

        # Make some movements
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Switch to command mode (pause)
        self.controller.enter_command_mode()
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)
        self.assertTrue(self.brain.is_mapping_active())

        # Resume mapping
        result = self.controller.execute_command(
            self.controller.parse_command(":resume")
        )

        self.assertIn("Resumed", result)
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)
        self.assertTrue(self.brain.is_mapping_active())

        # Continue mapping
        self.controller.handle_key_press("RIGHT")
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")


if __name__ == "__main__":
    unittest.main()
