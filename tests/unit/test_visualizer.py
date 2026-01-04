"""
Unit tests for the Visualizer module.
"""

import pytest
from src.visualizer import MapGrid, StatusBar
from src.cell import WorldMap, Cell
from src.controller import Mode
from typing import Tuple, List


class TestMapGrid:
    """Tests for the MapGrid widget."""

    def test_grid_initialization(self):
        """Test that MapGrid initializes with default 2x2 size."""
        grid = MapGrid()
        assert grid._grid_size == 2

    def test_calculate_bounds_empty_map(self):
        """Test bounds calculation with no data returns origin."""
        grid = MapGrid()
        grid._world_map = WorldMap()
        grid._robot_pos = None
        grid._current_path = []

        bounds = grid._calculate_bounds()
        assert bounds == (0, 0, 0, 0)  # Just the origin

    def test_calculate_bounds_with_cells(self):
        """Test bounds calculation with mapped cells."""
        grid = MapGrid()
        world_map = WorldMap()
        world_map.set_cell(0, 0, "Kitchen")
        world_map.set_cell(2, 3, "Living Room")
        world_map.set_cell(-1, -2, "Bedroom")

        grid._world_map = world_map
        grid._robot_pos = (0, 0)
        grid._current_path = []

        bounds = grid._calculate_bounds()
        assert bounds == (-1, 2, -2, 3)

    def test_calculate_bounds_with_path(self):
        """Test bounds calculation includes current path."""
        grid = MapGrid()
        world_map = WorldMap()
        world_map.set_cell(0, 0, "Kitchen")

        grid._world_map = world_map
        grid._robot_pos = (0, 0)
        grid._current_path = [(0, 0), (1, 0), (2, 0), (2, 1)]

        bounds = grid._calculate_bounds()
        assert bounds == (0, 2, 0, 1)

    def test_grid_size_growth_2_to_4(self):
        """Test grid grows from 2x2 to 4x4 when needed."""
        grid = MapGrid()
        world_map = WorldMap()

        # Add cells that fit in 2x2
        world_map.set_cell(0, 0, "Kitchen")
        world_map.set_cell(1, 1, "Kitchen")

        grid._world_map = world_map
        grid._robot_pos = (0, 0)
        grid._current_path = []
        grid._update_grid_size()

        assert grid._grid_size == 2  # Should still be 2

        # Add a cell that requires 4x4
        world_map.set_cell(2, 2, "Living Room")
        grid._update_grid_size()

        assert grid._grid_size == 4  # Should grow to 4

    def test_grid_size_growth_4_to_8(self):
        """Test grid grows from 4x4 to 8x8."""
        grid = MapGrid()
        world_map = WorldMap()

        # Add cells that require 8x8
        world_map.set_cell(0, 0, "Kitchen")
        world_map.set_cell(5, 5, "Bedroom")

        grid._world_map = world_map
        grid._robot_pos = (0, 0)
        grid._current_path = []
        grid._update_grid_size()

        assert grid._grid_size == 8  # Should be 8 to fit 6x6 area

    def test_grid_size_with_negative_coordinates(self):
        """Test grid sizing with negative coordinates."""
        grid = MapGrid()
        world_map = WorldMap()

        # Cells spanning from -2 to 2 (5 cells wide/tall)
        world_map.set_cell(-2, -2, "Room1")
        world_map.set_cell(2, 2, "Room2")

        grid._world_map = world_map
        grid._robot_pos = (0, 0)
        grid._current_path = []
        grid._update_grid_size()

        assert grid._grid_size == 8  # Need 8x8 to fit 5x5 area

    def test_get_cell_symbol_empty(self):
        """Test cell symbol for empty cell."""
        grid = MapGrid()
        grid._world_map = WorldMap()
        grid._robot_pos = None
        grid._current_path = []

        symbol = grid._get_cell_symbol(0, 0)
        assert symbol == '.'

    def test_get_cell_symbol_room(self):
        """Test cell symbol for room cell."""
        grid = MapGrid()
        world_map = WorldMap()
        world_map.set_cell(0, 0, "Kitchen")

        grid._world_map = world_map
        grid._robot_pos = None
        grid._current_path = []

        symbol = grid._get_cell_symbol(0, 0)
        assert symbol == 'K'  # First letter of Kitchen

    def test_get_cell_symbol_path(self):
        """Test cell symbol for current path."""
        grid = MapGrid()
        grid._world_map = WorldMap()
        grid._robot_pos = None
        grid._current_path = [(1, 1), (2, 1)]

        symbol = grid._get_cell_symbol(1, 1)
        assert symbol == '*'

    def test_get_cell_symbol_robot(self):
        """Test cell symbol for robot position (highest priority)."""
        grid = MapGrid()
        world_map = WorldMap()
        world_map.set_cell(0, 0, "Kitchen")  # Even with room

        grid._world_map = world_map
        grid._robot_pos = (0, 0)
        grid._robot_orientation = "NORTH"
        grid._current_path = [(0, 0)]  # Even in path

        symbol = grid._get_cell_symbol(0, 0)
        assert symbol == '^'  # Robot takes priority

    def test_get_orientation_arrow_all_directions(self):
        """Test orientation arrows for all directions."""
        grid = MapGrid()

        grid._robot_orientation = "NORTH"
        assert grid._get_orientation_arrow() == '^'

        grid._robot_orientation = "EAST"
        assert grid._get_orientation_arrow() == '>'

        grid._robot_orientation = "SOUTH"
        assert grid._get_orientation_arrow() == 'v'

        grid._robot_orientation = "WEST"
        assert grid._get_orientation_arrow() == '<'

    def test_update_map_data(self):
        """Test updating map data triggers size recalculation."""
        grid = MapGrid()
        world_map = WorldMap()
        world_map.set_cell(0, 0, "Kitchen")
        world_map.set_cell(3, 3, "Bedroom")

        grid.update_map_data(
            world_map=world_map,
            robot_pos=(0, 0),
            robot_orientation="NORTH",
            current_path=[(0, 0), (1, 0)]
        )

        assert grid._world_map == world_map
        assert grid._robot_pos == (0, 0)
        assert grid._robot_orientation == "NORTH"
        assert grid._current_path == [(0, 0), (1, 0)]
        assert grid._grid_size == 4  # Should grow to fit 4x4 area


class TestStatusBar:
    """Tests for the StatusBar widget."""

    def test_status_bar_initialization(self):
        """Test StatusBar initializes with default values."""
        status_bar = StatusBar()
        assert status_bar._mode == Mode.COMMAND_MODE
        assert status_bar._robot_pos == (0, 0)
        assert status_bar._robot_orientation == "NORTH"
        assert status_bar._current_room is None
        assert status_bar._message == "Type :help for commands"

    def test_status_bar_render_command_mode(self):
        """Test status bar renders correctly in command mode."""
        status_bar = StatusBar()
        # Set state directly without calling update()
        status_bar._mode = Mode.COMMAND_MODE
        status_bar._robot_pos = (1, 2)
        status_bar._robot_orientation = "WEST"
        status_bar._message = "Custom message"

        result = status_bar._render_status()
        # Check that the text contains expected elements
        text_str = str(result)
        assert "COMMAND" in text_str
        assert "(1, 2)" in text_str
        assert "WEST" in text_str
        assert "Custom message" in text_str

    def test_status_bar_render_mapping_mode(self):
        """Test status bar renders correctly in mapping mode with room."""
        status_bar = StatusBar()
        # Set state directly without calling update()
        status_bar._mode = Mode.MAPPING_MODE
        status_bar._robot_pos = (3, 5)
        status_bar._robot_orientation = "NORTH"
        status_bar._current_room = "Living Room"

        result = status_bar._render_status()
        text_str = str(result)
        assert "MAPPING" in text_str
        assert "(3, 5)" in text_str
        assert "NORTH" in text_str
        assert "Living Room" in text_str
