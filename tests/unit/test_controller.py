"""
Unit tests for Controller
"""

import unittest
import time
from unittest.mock import Mock
from src.controller import Controller, Mode, ParsedCommand
from src.brain import Brain
from src.robot import VacuumRobot
from src.cell import WorldMap
from src.constants import CalibrationConfig


class TestControllerMode(unittest.TestCase):
    """Test cases for Controller mode management"""

    def setUp(self):
        """Set up test fixtures"""
        self.controller = Controller()

    def test_default_mode_is_command(self):
        """Test that controller starts in command mode"""
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

    def test_enter_mapping_mode(self):
        """Test switching to mapping mode"""
        self.controller.enter_mapping_mode()
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

    def test_enter_command_mode(self):
        """Test switching to command mode"""
        self.controller.enter_mapping_mode()
        self.controller.enter_command_mode()
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

    def test_mode_switching(self):
        """Test switching between modes multiple times"""
        # Start in command mode
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

        # Switch to mapping
        self.controller.enter_mapping_mode()
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

        # Switch back to command
        self.controller.enter_command_mode()
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

        # Switch to mapping again
        self.controller.enter_mapping_mode()
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)


class TestCommandParsing(unittest.TestCase):
    """Test cases for command parsing"""

    def setUp(self):
        """Set up test fixtures"""
        self.controller = Controller()

    def test_parse_start_command_valid(self):
        """Test parsing valid :start command"""
        cmd = self.controller.parse_command(":start kitchen 0 0 NORTH")

        self.assertEqual(cmd.command, "start")
        self.assertEqual(cmd.params["room_name"], "kitchen")
        self.assertEqual(cmd.params["x"], 0)
        self.assertEqual(cmd.params["y"], 0)
        self.assertEqual(cmd.params["orientation"], "NORTH")

    def test_parse_start_command_negative_coordinates(self):
        """Test parsing :start command with negative coordinates"""
        cmd = self.controller.parse_command(":start bedroom -2 -3 SOUTH")

        self.assertEqual(cmd.command, "start")
        self.assertEqual(cmd.params["room_name"], "bedroom")
        self.assertEqual(cmd.params["x"], -2)
        self.assertEqual(cmd.params["y"], -3)
        self.assertEqual(cmd.params["orientation"], "SOUTH")

    def test_parse_start_command_lowercase_orientation(self):
        """Test that orientation is converted to uppercase"""
        cmd = self.controller.parse_command(":start room 1 2 east")

        self.assertEqual(cmd.params["orientation"], "EAST")

    def test_parse_start_command_all_orientations(self):
        """Test all valid orientations"""
        for orientation in ["NORTH", "SOUTH", "EAST", "WEST"]:
            cmd = self.controller.parse_command(f":start room 0 0 {orientation}")
            self.assertEqual(cmd.params["orientation"], orientation)

            # Test lowercase too
            cmd = self.controller.parse_command(f":start room 0 0 {orientation.lower()}")
            self.assertEqual(cmd.params["orientation"], orientation)

    def test_parse_start_command_missing_arguments(self):
        """Test that :start with missing arguments raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":start kitchen 0 0")

        self.assertIn("Invalid :start syntax", str(context.exception))

    def test_parse_start_command_extra_arguments(self):
        """Test that :start with extra arguments raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":start kitchen 0 0 NORTH extra")

        self.assertIn("Invalid :start syntax", str(context.exception))

    def test_parse_start_command_invalid_coordinates(self):
        """Test that non-integer coordinates raise error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":start kitchen abc 0 NORTH")

        self.assertIn("integers", str(context.exception))

    def test_parse_start_command_invalid_orientation(self):
        """Test that invalid orientation raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":start kitchen 0 0 NORTHWEST")

        self.assertIn("Invalid orientation", str(context.exception))

    def test_parse_save_command(self):
        """Test parsing :save command"""
        cmd = self.controller.parse_command(":save")

        self.assertEqual(cmd.command, "save")
        self.assertEqual(cmd.params, {})

    def test_parse_save_command_with_extra_arguments(self):
        """Test that :save with arguments raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":save extra")

        self.assertIn("Invalid :save syntax", str(context.exception))

    def test_parse_resume_command(self):
        """Test parsing :resume command"""
        cmd = self.controller.parse_command(":resume")

        self.assertEqual(cmd.command, "resume")
        self.assertEqual(cmd.params, {})

    def test_parse_resume_command_with_extra_arguments(self):
        """Test that :resume with arguments raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":resume extra")

        self.assertIn("Invalid :resume syntax", str(context.exception))

    def test_parse_command_without_colon(self):
        """Test that command without : raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command("start kitchen 0 0 NORTH")

        self.assertIn("must start with ':'", str(context.exception))

    def test_parse_empty_command(self):
        """Test that empty command raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command("")

        self.assertIn("Empty command", str(context.exception))

    def test_parse_colon_only(self):
        """Test that colon only raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":")

        self.assertIn("Empty command after ':'", str(context.exception))

    def test_parse_unknown_command(self):
        """Test that unknown command raises error"""
        with self.assertRaises(ValueError) as context:
            self.controller.parse_command(":unknown")

        self.assertIn("Unknown command", str(context.exception))

    def test_parse_command_with_whitespace(self):
        """Test that commands with leading/trailing whitespace are parsed correctly"""
        cmd = self.controller.parse_command("  :save  ")
        self.assertEqual(cmd.command, "save")

        cmd = self.controller.parse_command("  :start kitchen 0 0 NORTH  ")
        self.assertEqual(cmd.command, "start")
        self.assertEqual(cmd.params["room_name"], "kitchen")

    def test_parse_command_case_insensitive(self):
        """Test that command names are case insensitive"""
        cmd = self.controller.parse_command(":START kitchen 0 0 NORTH")
        self.assertEqual(cmd.command, "start")

        cmd = self.controller.parse_command(":Save")
        self.assertEqual(cmd.command, "save")

        cmd = self.controller.parse_command(":RESUME")
        self.assertEqual(cmd.command, "resume")


class TestParsedCommand(unittest.TestCase):
    """Test cases for ParsedCommand dataclass"""

    def test_parsed_command_creation(self):
        """Test creating a ParsedCommand"""
        cmd = ParsedCommand(
            command="start",
            params={"room_name": "kitchen", "x": 0, "y": 0, "orientation": "NORTH"}
        )

        self.assertEqual(cmd.command, "start")
        self.assertEqual(cmd.params["room_name"], "kitchen")
        self.assertEqual(cmd.params["x"], 0)

    def test_parsed_command_empty_params(self):
        """Test creating a ParsedCommand with empty params"""
        cmd = ParsedCommand(command="save", params={})

        self.assertEqual(cmd.command, "save")
        self.assertEqual(len(cmd.params), 0)


class TestKeyboardInput(unittest.TestCase):
    """Test cases for keyboard input handling"""

    def setUp(self):
        """Set up test fixtures"""
        # Create brain with all dependencies
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(speed_cm_per_sec=10.0, cell_size_cm=30.0)
        self.brain = Brain(self.robot, self.world_map, self.config)

        # Create controller with brain
        self.controller = Controller(self.brain)

    def test_controller_without_brain(self):
        """Test that controller can be created without brain"""
        controller = Controller()
        self.assertIsNone(controller._brain)

    def test_handle_key_press_without_brain_raises_error(self):
        """Test that key press without brain raises error"""
        controller = Controller()  # No brain
        controller.enter_mapping_mode()

        with self.assertRaises(RuntimeError) as context:
            controller.handle_key_press("UP")

        self.assertIn("Brain not connected", str(context.exception))

    def test_handle_turn_left(self):
        """Test left turn key press"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Press left key
        self.controller.handle_key_press("LEFT")

        # Orientation should change
        self.assertEqual(self.brain.get_orientation(), "WEST")

    def test_handle_turn_right(self):
        """Test right turn key press"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Press right key
        self.controller.handle_key_press("RIGHT")

        # Orientation should change
        self.assertEqual(self.brain.get_orientation(), "EAST")

    def test_handle_forward_press_and_release(self):
        """Test forward movement with press and release"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Press UP key
        self.controller.handle_key_press("UP")

        # Simulate holding long enough to cross cell boundary
        # At 10 cm/s with 30cm cells, need >= 3 seconds to cross 1 cell
        time.sleep(3.1)

        # Release UP key
        self.controller.handle_key_release("UP")

        # Position should have changed and crossed a cell boundary
        # Path should have recorded the movement
        path = self.brain.get_current_path()
        self.assertGreater(len(path), 1)

    def test_handle_colon_switches_to_command_mode(self):
        """Test that colon key switches to command mode"""
        self.controller.enter_mapping_mode()
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

        self.controller.handle_key_press("COLON")

        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

    def test_keys_ignored_in_command_mode(self):
        """Test that arrow keys are ignored in command mode"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_command_mode()

        initial_orientation = self.brain.get_orientation()

        # Try to press keys in command mode
        self.controller.handle_key_press("LEFT")
        self.controller.handle_key_press("RIGHT")

        # Orientation shouldn't change
        self.assertEqual(self.brain.get_orientation(), initial_orientation)

    def test_colon_works_in_command_mode_too(self):
        """Test that colon key works even in command mode"""
        self.controller.enter_command_mode()

        # Pressing colon again should keep us in command mode
        self.controller.handle_key_press("COLON")
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

    def test_key_press_case_insensitive(self):
        """Test that key names are case insensitive"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Lowercase key names should work
        self.controller.handle_key_press("left")
        self.assertEqual(self.brain.get_orientation(), "WEST")

        self.controller.handle_key_press("right")
        self.assertEqual(self.brain.get_orientation(), "NORTH")

    def test_multiple_turns(self):
        """Test multiple turn operations"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Full rotation
        self.controller.handle_key_press("RIGHT")  # NORTH -> EAST
        self.assertEqual(self.brain.get_orientation(), "EAST")

        self.controller.handle_key_press("RIGHT")  # EAST -> SOUTH
        self.assertEqual(self.brain.get_orientation(), "SOUTH")

        self.controller.handle_key_press("RIGHT")  # SOUTH -> WEST
        self.assertEqual(self.brain.get_orientation(), "WEST")

        self.controller.handle_key_press("RIGHT")  # WEST -> NORTH
        self.assertEqual(self.brain.get_orientation(), "NORTH")

    def test_forward_release_without_press(self):
        """Test that releasing UP without pressing doesn't cause error"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Release without press should not raise error
        self.controller.handle_key_release("UP")

        # Should still be at start position
        self.assertEqual(self.brain.get_position(), (0, 0))

    def test_complex_movement_sequence(self):
        """Test a complex sequence of movements and turns"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.controller.enter_mapping_mode()

        # Move forward - need to cross cell boundary
        self.controller.handle_key_press("UP")
        time.sleep(3.1)  # Move > 30cm to cross cell
        self.controller.handle_key_release("UP")

        # Turn right
        self.controller.handle_key_press("RIGHT")

        # Move forward again - need to cross another cell boundary
        self.controller.handle_key_press("UP")
        time.sleep(3.1)  # Move > 30cm to cross cell
        self.controller.handle_key_release("UP")

        # Should have moved and turned
        path = self.brain.get_current_path()
        self.assertGreater(len(path), 2)
        self.assertEqual(self.brain.get_orientation(), "EAST")


class TestCommandExecution(unittest.TestCase):
    """Test cases for command execution"""

    def setUp(self):
        """Set up test fixtures"""
        # Create brain with all dependencies
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(speed_cm_per_sec=10.0, cell_size_cm=30.0)
        self.brain = Brain(self.robot, self.world_map, self.config)

        # Create controller with brain
        self.controller = Controller(self.brain)

    def test_execute_command_without_brain_raises_error(self):
        """Test that executing command without brain raises error"""
        controller = Controller()  # No brain
        cmd = ParsedCommand(command="start", params={"room_name": "kitchen", "x": 0, "y": 0, "orientation": "NORTH"})

        with self.assertRaises(RuntimeError) as context:
            controller.execute_command(cmd)

        self.assertIn("Brain not connected", str(context.exception))

    def test_execute_start_command(self):
        """Test executing :start command"""
        cmd = self.controller.parse_command(":start kitchen 0 0 NORTH")

        result = self.controller.execute_command(cmd)

        # Check result message
        self.assertIn("Started mapping", result)
        self.assertIn("kitchen", result)

        # Check that brain started mapping
        self.assertTrue(self.brain.is_mapping_active())
        self.assertEqual(self.brain.get_position(), (0, 0))
        self.assertEqual(self.brain.get_orientation(), "NORTH")

        # Check mode switched to mapping
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

    def test_execute_start_command_with_negative_coords(self):
        """Test executing :start with negative coordinates"""
        # First create a room to allow starting at non-origin
        self.brain.start_mapping("room1", 0, 0, "NORTH")
        self.brain.record_movement(3.0)  # (0, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (0, 0)
        self.brain.save_room()

        # Now start mapping at a negative position
        cmd = self.controller.parse_command(":start room2 -1 -2 SOUTH")

        # This should fail because (-1, -2) doesn't exist
        with self.assertRaises(ValueError):
            self.controller.execute_command(cmd)

    def test_execute_save_command(self):
        """Test executing :save command"""
        # Start mapping
        self.controller.execute_command(
            self.controller.parse_command(":start kitchen 0 0 NORTH")
        )

        # Make some movements to create a rectangle (0,0) -> (0,2) -> (2,2) -> (2,0) -> close to (0,0)
        # Config: 10 cm/s speed, 30 cm cells -> need 3 seconds per cell

        # Move north 2 cells (6 seconds)
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Turn right (now facing EAST)
        self.controller.handle_key_press("RIGHT")

        # Move east 2 cells (6 seconds)
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Turn right (now facing SOUTH)
        self.controller.handle_key_press("RIGHT")

        # Move south 2 cells (6 seconds)
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Turn right (now facing WEST)
        self.controller.handle_key_press("RIGHT")

        # Move west 2 cells to close the shape (back to x=0)
        self.controller.handle_key_press("UP")
        time.sleep(6.0)
        self.controller.handle_key_release("UP")

        # Now we're at (0,0) - back to start, shape is closed
        # Now save
        cmd = self.controller.parse_command(":save")
        result = self.controller.execute_command(cmd)

        # Check result message
        self.assertIn("saved", result)
        self.assertIn("kitchen", result)

        # Check that mapping ended
        self.assertFalse(self.brain.is_mapping_active())

        # Check mode switched to command
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

        # Check room was saved to world map
        kitchen_cells = self.world_map.get_all_cells_for_room("kitchen")
        self.assertGreater(len(kitchen_cells), 0)

    def test_execute_save_without_mapping_raises_error(self):
        """Test that :save without active mapping raises error"""
        cmd = self.controller.parse_command(":save")

        with self.assertRaises(RuntimeError) as context:
            self.controller.execute_command(cmd)

        self.assertIn("No active mapping session", str(context.exception))

    def test_execute_resume_command(self):
        """Test executing :resume command"""
        # Start mapping
        self.controller.execute_command(
            self.controller.parse_command(":start bedroom 0 0 EAST")
        )

        # Switch to command mode (simulating pressing colon)
        self.controller.enter_command_mode()
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

        # Now resume
        cmd = self.controller.parse_command(":resume")
        result = self.controller.execute_command(cmd)

        # Check result message
        self.assertIn("Resumed", result)

        # Check mode switched back to mapping
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

        # Mapping should still be active
        self.assertTrue(self.brain.is_mapping_active())

    def test_execute_resume_without_mapping_raises_error(self):
        """Test that :resume without active mapping raises error"""
        cmd = self.controller.parse_command(":resume")

        with self.assertRaises(RuntimeError) as context:
            self.controller.execute_command(cmd)

        self.assertIn("No active mapping session", str(context.exception))

    def test_full_workflow_with_commands(self):
        """Test complete workflow: start -> map -> save"""
        # Start mapping
        result = self.controller.execute_command(
            self.controller.parse_command(":start office 0 0 NORTH")
        )
        self.assertIn("Started", result)
        self.assertEqual(self.controller.get_mode(), Mode.MAPPING_MODE)

        # Map a simple square (0,0) -> (0,1) -> (1,1) -> (1,0) -> close to (0,0)
        # Config: 10 cm/s speed, 30 cm cells -> need 3 seconds per cell

        # Move north 1 cell (3 seconds)
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Turn right (now facing EAST)
        self.controller.handle_key_press("RIGHT")

        # Move east 1 cell (3 seconds)
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Turn right (now facing SOUTH)
        self.controller.handle_key_press("RIGHT")

        # Move south 1 cell (3 seconds)
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Turn right (now facing WEST) - now we're at (1,0)
        self.controller.handle_key_press("RIGHT")

        # Move west 1 cell to close the shape (back to x=0)
        self.controller.handle_key_press("UP")
        time.sleep(3.0)
        self.controller.handle_key_release("UP")

        # Now we're at (0,0) - back to start, shape is closed
        # Save
        self.controller.enter_command_mode()
        result = self.controller.execute_command(
            self.controller.parse_command(":save")
        )
        self.assertIn("saved", result)
        self.assertEqual(self.controller.get_mode(), Mode.COMMAND_MODE)

        # Verify room exists
        self.assertIn("office", self.world_map.get_room_names())

    def test_parse_and_execute_combined(self):
        """Test parsing and executing in one flow"""
        # This simulates what the main loop will do
        command_string = ":start hallway 0 0 WEST"

        # Parse
        parsed = self.controller.parse_command(command_string)

        # Execute
        result = self.controller.execute_command(parsed)

        self.assertIn("hallway", result)
        self.assertTrue(self.brain.is_mapping_active())
        self.assertEqual(self.brain.get_orientation(), "WEST")


if __name__ == "__main__":
    unittest.main()
