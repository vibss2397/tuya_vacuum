"""
Unit tests for Brain
"""

import unittest
from src.brain import Brain
from src.robot import VacuumRobot
from src.room import WorldMap
from src.constants import CalibrationConfig
# Waypoint is no longer used


class TestBrain(unittest.TestCase):
    """Test cases for Brain class"""

    def setUp(self):
        """Set up test fixtures"""
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            cell_size_cm=30.0
        )
        self.brain = Brain(self.robot, self.world_map, self.config)

    def test_forward_movement_north(self):
        """Test forward movement updates position correctly when facing NORTH"""
        # Start at (0, 0) facing NORTH
        self.brain.set_position(0, 0, "NORTH")

        # Move forward for 3 seconds: 3s * 10cm/s = 30cm = 1 cell
        self.brain.update_position(3.0)

        # Should be at (0, 1)
        self.assertEqual(self.brain.get_position(), (0, 1))
        self.assertEqual(self.brain.get_orientation(), "NORTH")

    def test_forward_movement_east(self):
        """Test forward movement updates position correctly when facing EAST"""
        # Start at (0, 0) facing EAST
        self.brain.set_position(0, 0, "EAST")

        # Move forward for 6 seconds: 6s * 10cm/s = 60cm = 2 cells
        self.brain.update_position(6.0)

        # Should be at (2, 0)
        self.assertEqual(self.brain.get_position(), (2, 0))
        self.assertEqual(self.brain.get_orientation(), "EAST")

    def test_forward_movement_south(self):
        """Test forward movement updates position correctly when facing SOUTH"""
        # Start at (5, 5) facing SOUTH
        self.brain.set_position(5, 5, "SOUTH")

        # Move forward for 3 seconds: 1 cell
        self.brain.update_position(3.0)

        # Should be at (5, 4)
        self.assertEqual(self.brain.get_position(), (5, 4))
        self.assertEqual(self.brain.get_orientation(), "SOUTH")

    def test_forward_movement_west(self):
        """Test forward movement updates position correctly when facing WEST"""
        # Start at (5, 5) facing WEST
        self.brain.set_position(5, 5, "WEST")

        # Move forward for 3 seconds: 1 cell
        self.brain.update_position(3.0)

        # Should be at (4, 5)
        self.assertEqual(self.brain.get_position(), (4, 5))
        self.assertEqual(self.brain.get_orientation(), "WEST")

    def test_turn_left_from_north(self):
        """Test turning left updates orientation correctly"""
        self.brain.set_position(0, 0, "NORTH")

        self.brain.robot.turn_left()
        self.assertEqual(self.brain.get_orientation(), "WEST")

        self.brain.robot.turn_left()
        self.assertEqual(self.brain.get_orientation(), "SOUTH")

        self.brain.robot.turn_left()
        self.assertEqual(self.brain.get_orientation(), "EAST")

        self.brain.robot.turn_left()
        self.assertEqual(self.brain.get_orientation(), "NORTH")

    def test_turn_right_from_north(self):
        """Test turning right updates orientation correctly"""
        self.brain.set_position(0, 0, "NORTH")

        self.brain.robot.turn_right()
        self.assertEqual(self.brain.get_orientation(), "EAST")

        self.brain.robot.turn_right()
        self.assertEqual(self.brain.get_orientation(), "SOUTH")

        self.brain.robot.turn_right()
        self.assertEqual(self.brain.get_orientation(), "WEST")

        self.brain.robot.turn_right()
        self.assertEqual(self.brain.get_orientation(), "NORTH")

    def test_complex_movement_sequence(self):
        """Test a sequence of movements and turns"""
        # Start at (0, 0) facing NORTH
        self.brain.set_position(0, 0, "NORTH")

        # Move forward 1 cell
        self.brain.update_position(3.0)
        self.assertEqual(self.brain.get_position(), (0, 1))

        # Turn right (now facing EAST)
        self.brain.robot.turn_right()
        self.assertEqual(self.brain.get_orientation(), "EAST")

        # Move forward 2 cells
        self.brain.update_position(6.0)
        self.assertEqual(self.brain.get_position(), (2, 1))

        # Turn right (now facing SOUTH)
        self.brain.robot.turn_right()
        self.assertEqual(self.brain.get_orientation(), "SOUTH")

        # Move forward 1 cell
        self.brain.update_position(3.0)
        self.assertEqual(self.brain.get_position(), (2, 0))


class TestBrainPathRecording(unittest.TestCase):
    """Test cases for Brain path recording functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            cell_size_cm=30.0
        )
        self.brain = Brain(self.robot, self.world_map, self.config)

    def test_start_mapping_first_room_at_origin(self):
        """Test starting first room at (0,0) succeeds"""
        self.brain.start_mapping("living_room", 0, 0, "NORTH")

        self.assertTrue(self.brain.is_mapping_active())
        self.assertEqual(self.brain.get_position(), (0, 0))
        self.assertEqual(self.brain.get_orientation(), "NORTH")
        self.assertEqual(self.brain.get_current_path(), [(0, 0)])

    def test_start_mapping_first_room_not_at_origin_raises_error(self):
        """Test starting first room not at (0,0) raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.brain.start_mapping("living_room", 1, 1, "NORTH")

        self.assertIn("First room must start at position (0, 0)", str(context.exception))

    def test_start_mapping_subsequent_room_at_valid_cell(self):
        """Test starting subsequent room at valid mapped cell succeeds"""
        # Map first room - add some cells to world map
        self.world_map.set_cell(0, 0, "room1")
        self.world_map.set_cell(1, 0, "room1")
        self.world_map.set_cell(1, 1, "room1")

        # Start second room from a valid cell
        self.brain.start_mapping("room2", 1, 1, "EAST")

        self.assertTrue(self.brain.is_mapping_active())
        self.assertEqual(self.brain.get_position(), (1, 1))

    def test_start_mapping_subsequent_room_at_invalid_cell_raises_error(self):
        """Test starting subsequent room at unmapped cell raises ValueError"""
        # Map first room
        self.world_map.set_cell(0, 0, "room1")

        # Try to start second room from unmapped cell
        with self.assertRaises(ValueError) as context:
            self.brain.start_mapping("room2", 5, 5, "EAST")

        self.assertIn("not a valid mapped cell", str(context.exception))

    def test_record_movement_accumulates_path(self):
        """Test that record_movement accumulates positions correctly"""
        self.brain.start_mapping("living_room", 0, 0, "NORTH")

        # Move forward 1 cell (3 seconds)
        self.brain.record_movement(3.0)

        # Move forward 1 more cell
        self.brain.record_movement(3.0)

        path = self.brain.get_current_path()
        expected_path = [(0, 0), (0, 1), (0, 2)]
        self.assertEqual(path, expected_path)

    def test_record_movement_without_start_raises_error(self):
        """Test recording movement without starting mapping raises error"""
        with self.assertRaises(RuntimeError) as context:
            self.brain.record_movement(3.0)

        self.assertIn("mapping session not started", str(context.exception))

    def test_clear_path_resets_state(self):
        """Test that clear_path resets mapping state"""
        self.brain.start_mapping("living_room", 0, 0, "NORTH")
        self.brain.record_movement(3.0)

        self.brain.clear_path()

        self.assertFalse(self.brain.is_mapping_active())
        self.assertEqual(self.brain.get_current_path(), [])

    def test_complex_path_recording(self):
        """Test recording a complete rectangular path"""
        self.brain.start_mapping("bedroom", 0, 0, "NORTH")

        # Move north 2 cells
        self.brain.record_movement(3.0)
        self.brain.record_movement(3.0)

        # Turn right (EAST) and move 2 cells
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.record_movement(3.0)

        # Turn right (SOUTH) and move 2 cells
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.record_movement(3.0)

        # Turn right (WEST) and move 2 cells back to start
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.record_movement(3.0)

        path = self.brain.get_current_path()
        expected_path = [
            (0, 0), (0, 1), (0, 2),  # North
            (1, 2), (2, 2),           # East
            (2, 1), (2, 0),           # South
            (1, 0), (0, 0)            # West (back to start)
        ]
        self.assertEqual(path, expected_path)


class TestBrainShapeClosure(unittest.TestCase):
    """Test cases for Brain shape closure detection"""

    def setUp(self):
        """Set up test fixtures"""
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            cell_size_cm=30.0
        )
        self.brain = Brain(self.robot, self.world_map, self.config)

    def test_exact_closure_rectangle(self):
        """Test exact closure when returning to start position with a rectangle"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Trace a rectangle and return to (0, 0)
        self.brain.record_movement(3.0)  # (0, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (0, 0) - back at start

        # Should be closed (same position)
        self.assertTrue(self.brain.is_shape_closed(tolerance=0))

    def test_near_closure_with_tolerance(self):
        """Test near closure within tolerance (one cell away from start)"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Trace most of a rectangle, stop 1 cell before closing
        self.brain.record_movement(6.0)  # (0, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # (2, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # (2, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 0) - one cell away from start

        # Within tolerance of 1
        self.assertTrue(self.brain.is_shape_closed(tolerance=1))

        # Not within tolerance of 0
        self.assertFalse(self.brain.is_shape_closed(tolerance=0))

    def test_not_aligned_raises_error(self):
        """Test that non-aligned position raises ValueError"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Move to (1, 1) - not aligned with (0, 0)
        self.brain.record_movement(6.0)  # (0, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)

        # Should raise ValueError because not aligned
        with self.assertRaises(ValueError) as context:
            self.brain.is_shape_closed()

        self.assertIn("not aligned", str(context.exception))

    def test_straight_line_raises_error(self):
        """Test that a straight line path raises ValueError"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Move only in one dimension (straight line)
        self.brain.record_movement(3.0)  # (0, 1)
        self.brain.record_movement(3.0)  # (0, 2)
        self.brain.record_movement(3.0)  # (0, 3)

        # Should raise ValueError because path is a straight line
        with self.assertRaises(ValueError) as context:
            self.brain.is_shape_closed(tolerance=5)

        self.assertIn("straight line", str(context.exception))

    def test_insufficient_points_raises_error(self):
        """Test that path with fewer than 4 points raises ValueError"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Only 2 movements (3 points total including start)
        self.brain.record_movement(3.0)  # (0, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)

        # Should raise ValueError because fewer than 4 points
        with self.assertRaises(ValueError) as context:
            self.brain.is_shape_closed()

        self.assertIn("at least 4 points", str(context.exception))

    def test_closure_check_without_mapping_raises_error(self):
        """Test that checking closure without active mapping raises RuntimeError"""
        with self.assertRaises(RuntimeError) as context:
            self.brain.is_shape_closed()

        self.assertIn("mapping session not started", str(context.exception))

    def test_complete_rectangle_closure(self):
        """Test complete rectangular path returns to start and is closed"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Trace 2x3 rectangle
        self.brain.record_movement(6.0)  # (0, 2) - north
        self.brain.robot.turn_right()
        self.brain.record_movement(9.0)  # (3, 2) - east
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # (3, 0) - south
        self.brain.robot.turn_right()
        self.brain.record_movement(9.0)  # (0, 0) - west, back at start

        # Should be exactly closed
        self.assertTrue(self.brain.is_shape_closed(tolerance=0))

    def test_l_shape_closure(self):
        """Test L-shaped path that closes properly"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Trace an L-shape
        self.brain.record_movement(6.0)  # (0, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.robot.turn_left()
        self.brain.record_movement(3.0)  # (2, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (2, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # (0, 0) - back at start
        # Should be closed
        self.assertTrue(self.brain.is_shape_closed(tolerance=0))


class TestBrainSaveRoom(unittest.TestCase):
    """Test cases for Brain save_room functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            cell_size_cm=30.0
        )
        self.brain = Brain(self.robot, self.world_map, self.config)

    def test_save_simple_rectangle(self):
        """Test saving a simple rectangular room"""
        self.brain.start_mapping("bedroom", 0, 0, "NORTH")

        # Trace a 2x2 rectangle
        self.brain.record_movement(6.0)  # (0, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # (2, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(6.0)  # (2, 0)
        self.brain.robot.turn_right()
        # Don't move back to start - test auto-close with tolerance

        # Save the room (should auto-close the 2-cell gap)
        self.brain.save_room(tolerance=2)

        # Verify room was saved
        bedroom_cells = self.world_map.get_all_cells_for_room("bedroom")
        self.assertEqual(len(bedroom_cells), 9)  # 3x3 cells

        # Verify corners are included
        self.assertTrue(self.world_map.cell_exists(0, 0))
        self.assertTrue(self.world_map.cell_exists(0, 2))
        self.assertTrue(self.world_map.cell_exists(2, 0))
        self.assertTrue(self.world_map.cell_exists(2, 2))

        # Verify interior cell is included
        self.assertTrue(self.world_map.cell_exists(1, 1))
        self.assertIn("bedroom", self.world_map.get_cell(1, 1).room_names)

        # Verify mapping session ended
        self.assertFalse(self.brain.is_mapping_active())

    def test_save_exact_closure(self):
        """Test saving when path returns exactly to start"""
        self.brain.start_mapping("kitchen", 0, 0, "NORTH")

        # Trace rectangle and return exactly to start
        self.brain.record_movement(3.0)  # (0, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (0, 0) - exactly at start

        # Save with no tolerance needed
        self.brain.save_room(tolerance=0)

        # Verify 4 cells saved (perimeter only for 1x1 square)
        kitchen_cells = self.world_map.get_all_cells_for_room("kitchen")
        self.assertEqual(len(kitchen_cells), 4)

    def test_save_l_shape(self):
        """Test saving an L-shaped room"""
        self.brain.start_mapping("hallway", 0, 0, "NORTH")

        # Trace L-shape
        self.brain.record_movement(6.0)  # (0, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 2)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.robot.turn_left()
        self.brain.record_movement(3.0)  # (2, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (2, 0)
        self.brain.robot.turn_right()
        # End at (2, 0), need to close back to (0, 0)

        # Save with tolerance to auto-close
        self.brain.save_room(tolerance=2)

        # Verify L-shape cells are saved (8 cells)
        hallway_cells = self.world_map.get_all_cells_for_room("hallway")
        self.assertEqual(len(hallway_cells), 8)

        # Verify key L-shape cells
        self.assertTrue(self.world_map.cell_exists(0, 0))
        self.assertTrue(self.world_map.cell_exists(0, 2))
        self.assertTrue(self.world_map.cell_exists(1, 1))
        self.assertTrue(self.world_map.cell_exists(2, 0))

    def test_save_without_mapping_raises_error(self):
        """Test that saving without active mapping raises RuntimeError"""
        with self.assertRaises(RuntimeError) as context:
            self.brain.save_room()

        self.assertIn("mapping session not started", str(context.exception))

    def test_save_unclosed_shape_raises_error(self):
        """Test that saving a shape that's too far from start raises ValueError"""
        self.brain.start_mapping("room", 0, 0, "NORTH")

        # Create path but end far from start
        self.brain.record_movement(9.0)  # (0, 3)
        self.brain.robot.turn_right()
        self.brain.record_movement(9.0)  # (3, 3)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (3, 2)
        # End at (3, 2), which is not aligned or close to (0, 0)

        # Should raise ValueError with tolerance=1
        with self.assertRaises(ValueError) as context:
            self.brain.save_room(tolerance=1)

        self.assertIn("not aligned", str(context.exception))

    def test_save_subsequent_room(self):
        """Test saving a second room that starts from first room's cell"""
        # First, save a room
        self.brain.start_mapping("room1", 0, 0, "NORTH")
        self.brain.record_movement(3.0)  # (0, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (0, 0)
        self.brain.save_room(tolerance=0)

        # Verify room1 has 4 cells initially
        room1_cells_initial = self.world_map.get_all_cells_for_room("room1")
        self.assertEqual(len(room1_cells_initial), 4)

        # Now start second room from a cell in room1
        # This will overlap with room1 at (1, 1) and (1, 0)
        self.brain.start_mapping("room2", 1, 1, "EAST")
        self.brain.record_movement(3.0)  # (2, 1)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (2, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)  # (1, 1)
        self.brain.save_room(tolerance=0)

        # After room2 is saved, overlapping cells belong to BOTH rooms
        room1_cells = self.world_map.get_all_cells_for_room("room1")
        room2_cells = self.world_map.get_all_cells_for_room("room2")

        # room1 has all its original cells: (0, 0), (0, 1), (1, 0), (1, 1)
        self.assertEqual(len(room1_cells), 4)
        # room2 has 4 cells: (1, 0), (1, 1), (2, 0), (2, 1)
        self.assertEqual(len(room2_cells), 4)

        # Overlapping cells belong to BOTH rooms (shared boundary)
        self.assertIn("room1", self.world_map.get_cell(1, 1).room_names)
        self.assertIn("room2", self.world_map.get_cell(1, 1).room_names)
        self.assertIn("room1", self.world_map.get_cell(1, 0).room_names)
        self.assertIn("room2", self.world_map.get_cell(1, 0).room_names)

        # Non-overlapping room1 cells belong only to room1
        self.assertIn("room1", self.world_map.get_cell(0, 0).room_names)
        self.assertEqual(len(self.world_map.get_cell(0, 0).room_names), 1)
        self.assertIn("room1", self.world_map.get_cell(0, 1).room_names)
        self.assertEqual(len(self.world_map.get_cell(0, 1).room_names), 1)

    def test_save_clears_path(self):
        """Test that saving a room clears the current path"""
        self.brain.start_mapping("room", 0, 0, "NORTH")
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)

        # Path should have points before save
        self.assertTrue(len(self.brain.get_current_path()) > 0)

        self.brain.save_room(tolerance=0)

        # Path should be empty after save
        self.assertEqual(len(self.brain.get_current_path()), 0)
        self.assertFalse(self.brain.is_mapping_active())


class TestBrainWaypoints(unittest.TestCase):
    """Test cases for waypoint tracking in Brain"""

    def setUp(self):
        """Set up test fixtures"""
        self.robot = VacuumRobot()
        self.world_map = WorldMap()
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        self.brain = Brain(self.robot, self.world_map, self.config)

    def test_waypoints_recorded_on_start(self):
        """Test that initial waypoint is recorded when starting mapping"""
        self.brain.start_mapping("test_room", 0, 0, "NORTH")

        # WorldMap should have waypoints after save
        waypoints = self.world_map.get_room_waypoints("test_room")
        # Before save, waypoints are only in Brain, not in WorldMap yet
        self.assertEqual(len(waypoints), 0)

    def test_waypoints_recorded_on_movement(self):
        """Test that waypoints are recorded during movement"""
        self.brain.start_mapping("test_room", 0, 0, "NORTH")

        # Move forward
        self.brain.record_movement(1.0)  # 10cm
        self.brain.record_movement(1.0)  # 10cm more

        # Save the room to store waypoints
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(1.0)
        self.brain.save_room()

        # Check waypoints were stored
        waypoints = self.world_map.get_room_waypoints("test_room")
        self.assertGreater(len(waypoints), 0)

        # Check waypoint properties
        for wp in waypoints:
            self.assertIsInstance(wp, Waypoint)
            self.assertIsInstance(wp.x_cm, float)
            self.assertIsInstance(wp.y_cm, float)
            self.assertIn(wp.orientation, ["NORTH", "SOUTH", "EAST", "WEST"])

    def test_waypoints_recorded_on_turns(self):
        """Test that waypoints are recorded when turning"""
        self.brain.start_mapping("test_room", 0, 0, "NORTH")

        # Turn several times
        self.brain.robot.turn_right()  # Now EAST
        self.brain.robot.turn_right()  # Now SOUTH
        self.brain.robot.turn_left()   # Now EAST

        # Move to complete the shape
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.save_room()

        # Check waypoints were stored with different orientations
        waypoints = self.world_map.get_room_waypoints("test_room")
        orientations = [wp.orientation for wp in waypoints]

        # Should have multiple different orientations
        self.assertGreater(len(set(orientations)), 1)

    def test_waypoints_capture_subcell_movements(self):
        """Test that waypoints capture sub-cell movements"""
        self.brain.start_mapping("test_room", 0, 0, "NORTH")

        # Move less than one cell (30cm)
        self.brain.record_movement(1.0)  # 10cm
        self.brain.robot.turn_right()
        self.brain.record_movement(1.0)  # 10cm east

        # Complete the room
        self.brain.record_movement(2.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.save_room()

        # Check waypoints exist
        waypoints = self.world_map.get_room_waypoints("test_room")
        self.assertGreater(len(waypoints), 3)

        # Verify precise cm positions (not just cell coordinates)
        for wp in waypoints:
            # Waypoints should have sub-cell precision
            self.assertIsInstance(wp.x_cm, float)
            self.assertIsInstance(wp.y_cm, float)

    def test_waypoints_cleared_after_save(self):
        """Test that internal waypoints are cleared after save"""
        self.brain.start_mapping("room1", 0, 0, "NORTH")
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.save_room()

        # Start a new room - waypoints should be fresh
        self.brain.start_mapping("room2", 1, 1, "NORTH")
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.robot.turn_right()
        self.brain.record_movement(3.0)
        self.brain.save_room()

        # Both rooms should have waypoints
        room1_waypoints = self.world_map.get_room_waypoints("room1")
        room2_waypoints = self.world_map.get_room_waypoints("room2")

        self.assertGreater(len(room1_waypoints), 0)
        self.assertGreater(len(room2_waypoints), 0)
        # They should be different
        self.assertNotEqual(room1_waypoints, room2_waypoints)


if __name__ == "__main__":
    unittest.main()
