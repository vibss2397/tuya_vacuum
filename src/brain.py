"""
Brain Module

The core mapping logic that tracks robot state and manages the world map.
"""

from typing import Tuple, List, Optional
from src.robot import VirtualRobot
from src.cell import WorldMap
from src.constants import CalibrationConfig
from src.polygon_fill import fill_polygon


class Brain:
    """
    The Brain manages robot state and coordinates the mapping process.

    It tracks the robot's current position and orientation, and translates
    timed movements into grid cell updates.
    """

    def __init__(self, robot: VirtualRobot, world_map: WorldMap, config: CalibrationConfig):
        """
        Initialize the Brain.

        Args:
            robot (VirtualRobot): The robot to control
            world_map (WorldMap): The map to update
            config (CalibrationConfig): Calibration constants
        """
        self.robot = robot
        self.world_map = world_map
        self.config = config

        # Current robot state
        self._current_x = 0
        self._current_y = 0
        self._current_orientation = "NORTH"

        # Path recording
        self._current_path: List[Tuple[int, int]] = []
        self._mapping_active = False
        self._current_room_name: Optional[str] = None
        self._start_position: Optional[Tuple[int, int]] = None

    def get_position(self) -> Tuple[int, int]:
        """
        Get the current robot position.

        Returns:
            Tuple[int, int]: Current (x, y) coordinates
        """
        return (self._current_x, self._current_y)

    def get_orientation(self) -> str:
        """
        Get the current robot orientation.

        Returns:
            str: Current orientation (NORTH/SOUTH/EAST/WEST)
        """
        return self._current_orientation

    def set_position(self, x: int, y: int, orientation: str):
        """
        Set the robot position and orientation.

        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            orientation (str): Orientation (NORTH/SOUTH/EAST/WEST)
        """
        self._current_x = x
        self._current_y = y
        self._current_orientation = orientation
        self.robot.set_position(x, y)
        self.robot.set_orientation(orientation)

    def update_position(self, duration: float):
        """
        Update robot position based on forward movement duration.

        Calculates how many cells the robot moved based on the duration
        and current calibration settings, then updates position accordingly.

        Args:
            duration (float): Duration of movement in seconds
        """
        # Calculate distance traveled
        distance_cm = duration * self.config.speed_cm_per_sec

        # Convert to cells
        cells_moved = round(distance_cm / self.config.cell_size_cm)

        # Update position based on orientation
        if self._current_orientation == "NORTH":
            self._current_y += cells_moved
        elif self._current_orientation == "SOUTH":
            self._current_y -= cells_moved
        elif self._current_orientation == "EAST":
            self._current_x += cells_moved
        elif self._current_orientation == "WEST":
            self._current_x -= cells_moved

        # Update robot's internal state
        self.robot.set_position(self._current_x, self._current_y)

    def turn_left(self):
        """
        Turn the robot 90 degrees to the left.

        Updates orientation: NORTH → WEST → SOUTH → EAST → NORTH
        """
        orientation_cycle = {
            "NORTH": "WEST",
            "WEST": "SOUTH",
            "SOUTH": "EAST",
            "EAST": "NORTH"
        }
        self._current_orientation = orientation_cycle[self._current_orientation]
        self.robot.set_orientation(self._current_orientation)

    def turn_right(self):
        """
        Turn the robot 90 degrees to the right.

        Updates orientation: NORTH → EAST → SOUTH → WEST → NORTH
        """
        orientation_cycle = {
            "NORTH": "EAST",
            "EAST": "SOUTH",
            "SOUTH": "WEST",
            "WEST": "NORTH"
        }
        self._current_orientation = orientation_cycle[self._current_orientation]
        self.robot.set_orientation(self._current_orientation)

    def start_mapping(self, room_name: str, x: int, y: int, orientation: str):
        """
        Start a new mapping session for a room.

        Validates starting position and initializes path recording.

        Args:
            room_name (str): Name of the room to map
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            orientation (str): Starting orientation

        Raises:
            ValueError: If first room doesn't start at (0,0) or if starting
                       position is invalid for subsequent rooms
        """
        # Validation: first room must start at (0,0)
        if len(self.world_map.get_room_names()) == 0:
            if x != 0 or y != 0:
                raise ValueError("First room must start at position (0, 0)")
        else:
            # Subsequent rooms must start at a valid mapped cell
            if not self.world_map.cell_exists(x, y):
                raise ValueError(f"Starting position ({x}, {y}) is not a valid mapped cell")

        # Initialize mapping session
        self._mapping_active = True
        self._current_room_name = room_name
        self._start_position = (x, y)
        self._current_path = [(x, y)]

        # Set robot position
        self.set_position(x, y, orientation)

    def record_movement(self, duration: float):
        """
        Record a forward movement during mapping.

        Updates position and appends to current path.

        Args:
            duration (float): Duration of movement in seconds

        Raises:
            RuntimeError: If mapping is not active
        """
        if not self._mapping_active:
            raise RuntimeError("Cannot record movement: mapping session not started")

        # Update position
        self.update_position(duration)

        # Record current position in path
        current_pos = self.get_position()
        self._current_path.append(current_pos)

    def get_current_path(self) -> List[Tuple[int, int]]:
        """
        Get the current recorded path.

        Returns:
            List[Tuple[int, int]]: List of (x, y) positions in the path
        """
        return self._current_path.copy()

    def clear_path(self):
        """
        Clear the current path and end mapping session.
        """
        self._current_path = []
        self._mapping_active = False
        self._current_room_name = None
        self._start_position = None

    def is_mapping_active(self) -> bool:
        """
        Check if a mapping session is currently active.

        Returns:
            bool: True if mapping is active, False otherwise
        """
        return self._mapping_active

    def is_shape_closed(self, tolerance: int = 0) -> bool:
        """
        Check if the traced path forms a closed 2D shape.

        The shape is considered closed if:
        1. Path has at least 4 points (minimum for a 2D shape)
        2. Path covers both X and Y dimensions (not just a straight line)
        3. Current position is aligned with start position (same x OR same y)
        4. Current position is within tolerance cells of start position

        Args:
            tolerance (int): Maximum distance (in cells) from start to consider closed

        Returns:
            bool: True if shape is closed or nearly closed, False otherwise

        Raises:
            RuntimeError: If mapping is not active
            ValueError: If path is invalid (not aligned, insufficient points, or not 2D)
        """
        if not self._mapping_active:
            raise RuntimeError("Cannot check closure: mapping session not started")

        if self._start_position is None:
            raise RuntimeError("Start position not set")

        # Check minimum path length (at least 4 points for a shape)
        if len(self._current_path) < 4:
            raise ValueError(
                f"Cannot close shape: path has only {len(self._current_path)} points. "
                f"Need at least 4 points to form a 2D shape."
            )

        # Check that path covers both X and Y dimensions (not just a line)
        x_coords = set(pos[0] for pos in self._current_path)
        y_coords = set(pos[1] for pos in self._current_path)

        if len(x_coords) == 1 or len(y_coords) == 1:
            raise ValueError(
                "Cannot close shape: path is a straight line. "
                "A valid room must be a 2D shape covering both X and Y dimensions."
            )

        current_pos = self.get_position()
        start_x, start_y = self._start_position
        current_x, current_y = current_pos

        # Check if aligned (same x OR same y)
        is_aligned = (current_x == start_x) or (current_y == start_y)

        if not is_aligned:
            raise ValueError(
                f"Cannot close shape: current position {current_pos} is not aligned "
                f"with start position {self._start_position}. "
                f"Robot must be in a straight line (same x OR same y) with the starting point."
            )

        # Calculate Manhattan distance along the aligned axis
        if current_x == start_x:
            # Vertical alignment
            distance = abs(current_y - start_y)
        else:
            # Horizontal alignment
            distance = abs(current_x - start_x)

        return distance <= tolerance

    def save_room(self, tolerance: int = 1):
        """
        Save the currently mapped room to the world map.

        This method:
        1. Validates that the shape is closed (or nearly closed within tolerance)
        2. Auto-closes the shape by connecting current position to start if needed
        3. Uses polygon fill to find all interior cells
        4. Assigns all cells (perimeter + interior) to the current room
        5. Clears the current path and ends the mapping session

        Args:
            tolerance (int): Maximum distance from start position to auto-close shape.
                           Default is 1 cell.

        Raises:
            RuntimeError: If mapping session is not active
            ValueError: If shape cannot be closed (not aligned, insufficient points, etc.)
        """
        if not self._mapping_active:
            raise RuntimeError("Cannot save room: mapping session not started")

        if self._current_room_name is None:
            raise RuntimeError("Cannot save room: no room name set")

        # Check if shape is closed or can be auto-closed
        if not self.is_shape_closed(tolerance=tolerance):
            raise ValueError(
                f"Cannot save room: shape is not closed. Current position "
                f"{self.get_position()} is more than {tolerance} cells away from "
                f"start position {self._start_position}"
            )

        # Auto-close the shape by adding final segment back to start
        # (only if current position is not already at start)
        path_to_fill = self._current_path.copy()
        if self.get_position() != self._start_position:
            # Add intermediate points to close the gap
            current_x, current_y = self.get_position()
            start_x, start_y = self._start_position

            if current_x == start_x:
                # Vertical closing - add points along y-axis
                y_step = 1 if start_y > current_y else -1
                for y in range(current_y + y_step, start_y, y_step):
                    path_to_fill.append((current_x, y))
            else:
                # Horizontal closing - add points along x-axis
                x_step = 1 if start_x > current_x else -1
                for x in range(current_x + x_step, start_x, x_step):
                    path_to_fill.append((x, current_y))

        # Fill the polygon to get all interior and perimeter cells
        filled_cells = fill_polygon(path_to_fill)

        # Assign all cells to this room in the world map
        for x, y in filled_cells:
            self.world_map.set_cell(x, y, self._current_room_name)

        # Clear the current path and end mapping session
        self.clear_path()
