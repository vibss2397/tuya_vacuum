"""
Cell and World Map Data Structures

Manages the grid-based map of the house.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List


@dataclass
class Cell:
    """
    Represents a single cell in the grid map.

    Attributes:
        x (int): X-coordinate of the cell
        y (int): Y-coordinate of the cell
        room_name (Optional[str]): Name of the room this cell belongs to
    """

    x: int
    y: int
    room_name: Optional[str] = None


class WorldMap:
    """
    Manages the grid-based world map.

    Uses a dictionary for sparse storage - only stores cells that have been mapped.
    """

    def __init__(self):
        """Initialize an empty world map."""
        self._cells: Dict[Tuple[int, int], Cell] = {}

    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """
        Get a cell at the specified coordinates.

        Args:
            x (int): X-coordinate
            y (int): Y-coordinate

        Returns:
            Optional[Cell]: Cell at the coordinates, or None if not mapped
        """
        return self._cells.get((x, y))

    def set_cell(self, x: int, y: int, room_name: Optional[str] = None) -> Cell:
        """
        Set or update a cell at the specified coordinates.

        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            room_name (Optional[str]): Name of the room

        Returns:
            Cell: The cell that was set
        """
        cell = Cell(x=x, y=y, room_name=room_name)
        self._cells[(x, y)] = cell
        return cell

    def cell_exists(self, x: int, y: int) -> bool:
        """
        Check if a cell exists at the specified coordinates.

        Args:
            x (int): X-coordinate
            y (int): Y-coordinate

        Returns:
            bool: True if cell exists, False otherwise
        """
        return (x, y) in self._cells

    def get_all_cells_for_room(self, room_name: str) -> List[Cell]:
        """
        Get all cells belonging to a specific room.

        Args:
            room_name (str): Name of the room

        Returns:
            List[Cell]: List of cells in the room
        """
        return [
            cell for cell in self._cells.values()
            if cell.room_name == room_name
        ]

    def get_all_cells(self) -> List[Cell]:
        """
        Get all cells in the map.

        Returns:
            List[Cell]: List of all cells
        """
        return list(self._cells.values())

    def get_room_names(self) -> List[str]:
        """
        Get list of all unique room names in the map.

        Returns:
            List[str]: List of room names
        """
        room_names = set()
        for cell in self._cells.values():
            if cell.room_name:
                room_names.add(cell.room_name)
        return sorted(list(room_names))
