"""
Unit tests for Cell and WorldMap
"""

import unittest
from src.cell import Cell, WorldMap


class TestCell(unittest.TestCase):
    """Test cases for Cell dataclass"""

    def test_cell_creation_with_room(self):
        """Test creating a cell with room assignment"""
        cell = Cell(x=5, y=10, room_names={"living_room"})

        self.assertEqual(cell.x, 5)
        self.assertEqual(cell.y, 10)
        self.assertIn("living_room", cell.room_names)

    def test_cell_creation_without_room(self):
        """Test creating a cell without room assignment"""
        cell = Cell(x=3, y=7)

        self.assertEqual(cell.x, 3)
        self.assertEqual(cell.y, 7)
        self.assertEqual(len(cell.room_names), 0)


class TestWorldMap(unittest.TestCase):
    """Test cases for WorldMap class"""

    def test_add_and_retrieve_cell(self):
        """Test adding and retrieving cells from map"""
        world_map = WorldMap()

        # Add a cell
        cell = world_map.set_cell(x=0, y=0, room_name="bedroom")

        # Retrieve the cell
        retrieved = world_map.get_cell(0, 0)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.x, 0)
        self.assertEqual(retrieved.y, 0)
        self.assertIn("bedroom", retrieved.room_names)

    def test_get_nonexistent_cell_returns_none(self):
        """Test retrieving a cell that doesn't exist returns None"""
        world_map = WorldMap()

        result = world_map.get_cell(10, 10)

        self.assertIsNone(result)

    def test_cell_exists(self):
        """Test checking if a cell exists"""
        world_map = WorldMap()

        # Cell doesn't exist initially
        self.assertFalse(world_map.cell_exists(5, 5))

        # Add cell
        world_map.set_cell(5, 5, "kitchen")

        # Cell now exists
        self.assertTrue(world_map.cell_exists(5, 5))

    def test_get_all_cells_for_room(self):
        """Test querying cells by room name"""
        world_map = WorldMap()

        # Add cells to different rooms
        world_map.set_cell(0, 0, "bedroom")
        world_map.set_cell(0, 1, "bedroom")
        world_map.set_cell(1, 0, "kitchen")
        world_map.set_cell(1, 1, "bedroom")

        # Get bedroom cells
        bedroom_cells = world_map.get_all_cells_for_room("bedroom")

        self.assertEqual(len(bedroom_cells), 3)
        for cell in bedroom_cells:
            self.assertIn("bedroom", cell.room_names)

    def test_get_all_cells(self):
        """Test getting all cells from map"""
        world_map = WorldMap()

        # Add multiple cells
        world_map.set_cell(0, 0, "room1")
        world_map.set_cell(1, 1, "room2")
        world_map.set_cell(2, 2, "room3")

        all_cells = world_map.get_all_cells()

        self.assertEqual(len(all_cells), 3)

    def test_get_room_names(self):
        """Test getting list of all room names"""
        world_map = WorldMap()

        # Add cells to different rooms
        world_map.set_cell(0, 0, "bedroom")
        world_map.set_cell(1, 1, "kitchen")
        world_map.set_cell(2, 2, "bedroom")  # duplicate room name
        world_map.set_cell(3, 3, "bathroom")

        room_names = world_map.get_room_names()

        # Should have 3 unique room names, sorted
        self.assertEqual(len(room_names), 3)
        self.assertIn("bedroom", room_names)
        self.assertIn("kitchen", room_names)
        self.assertIn("bathroom", room_names)
        self.assertEqual(room_names, sorted(room_names))

    def test_shared_boundary_cells(self):
        """Test that cells can belong to multiple rooms (shared boundaries)"""
        world_map = WorldMap()

        # Add a cell to room1
        world_map.set_cell(5, 5, "room1")

        # Add the same cell to room2 (shared boundary)
        world_map.set_cell(5, 5, "room2")

        # Retrieve the cell
        cell = world_map.get_cell(5, 5)

        # Cell should belong to both rooms
        self.assertEqual(len(cell.room_names), 2)
        self.assertIn("room1", cell.room_names)
        self.assertIn("room2", cell.room_names)

        # Both room queries should return this cell
        room1_cells = world_map.get_all_cells_for_room("room1")
        room2_cells = world_map.get_all_cells_for_room("room2")
        self.assertIn(cell, room1_cells)
        self.assertIn(cell, room2_cells)


if __name__ == "__main__":
    unittest.main()
