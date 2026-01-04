"""
Brain Module

The core mapping logic that tracks robot state and manages the world map.
"""

from typing import Tuple, List, Optional
from src.robot import VacuumRobot
from src.room import WorldMap, Room, Point
from src.constants import CalibrationConfig


class Brain:
    """
    The Brain manages robot state and coordinates the mapping process.

    It tracks the robot's current position and orientation, and translates
    timed movements into grid cell updates.
    """

    def __init__(self, robot: VacuumRobot, world_map: WorldMap, config: CalibrationConfig):
        """
        Initialize the Brain.

        Args:
            robot (VacuumRobot): The robot to control
            world_map (WorldMap): The map to update
            config (CalibrationConfig): Calibration constants
        """
        self.robot = robot
        self.world_map = world_map
        self.config = config

        # Current robot state (stored in cm for precision)
        self._position_x_cm: float = 0.0
        self._position_y_cm: float = 0.0
        self._current_orientation = "NORTH"

        # Path recording (cm-level precision)
        # Each entry is (x_cm, y_cm, orientation)
        self._current_path_cm: List[Tuple[float, float, str]] = []
        self._mapping_active = False
        self._current_room_name: Optional[str] = None
        self._start_position_cm: Optional[Tuple[float, float]] = None

    def _cm_to_cell(self, cm: float) -> int:
        """
        Convert a position in cm to a grid cell coordinate (for visualization).

        Args:
            cm (float): Position in centimeters

        Returns:
            int: Grid cell coordinate (floor division)
        """
        return int(cm // self.config.cell_size_cm)

    def get_position(self) -> Tuple[int, int]:
        """
        Get the current robot position in grid cells.

        Converts internal cm position to grid cell coordinates.

        Returns:
            Tuple[int, int]: Current (x, y) grid cell coordinates
        """
        return (self._cm_to_cell(self._position_x_cm),
                self._cm_to_cell(self._position_y_cm))

    def get_position_cm(self) -> Tuple[float, float]:
        """
        Get the current robot position in centimeters (precise).

        Returns:
            Tuple[float, float]: Current (x, y) position in cm
        """
        return (self._position_x_cm, self._position_y_cm)

    def get_orientation(self) -> str:
        """
        Get the current robot orientation.

        Returns:
            str: Current orientation (NORTH/SOUTH/EAST/WEST)
        """
        return self._current_orientation

    def set_position(self, x: int, y: int, orientation: str):
        """
        Set the robot position and orientation (DEPRECATED - use set_position_cm).

        Accepts grid cell coordinates and converts to cm internally.

        Args:
            x (int): X-coordinate (grid cell)
            y (int): Y-coordinate (grid cell)
            orientation (str): Orientation (NORTH/SOUTH/EAST/WEST)
        """
        # Convert cell coordinates to cm (center of cell)
        self._position_x_cm = x * self.config.cell_size_cm
        self._position_y_cm = y * self.config.cell_size_cm
        self._current_orientation = orientation

        # Update robot with cm coordinates
        self.robot.set_position(self._position_x_cm, self._position_y_cm)
        self.robot.set_orientation(orientation)

    def set_position_cm(self, x_cm: float, y_cm: float, orientation: str):
        """
        Set the robot position and orientation using cm coordinates.

        For use with real robot sensors that report precise positions.

        Args:
            x_cm (float): X-coordinate in centimeters
            y_cm (float): Y-coordinate in centimeters
            orientation (str): Orientation (NORTH/SOUTH/EAST/WEST)
        """
        self._position_x_cm = x_cm
        self._position_y_cm = y_cm
        self._current_orientation = orientation

        # Update robot with cm coordinates
        self.robot.set_position(x_cm, y_cm)
        self.robot.set_orientation(orientation)

    def update_position(self, duration: float):
        """
        Update robot position based on forward movement duration.

        Calculates distance traveled in cm and updates precise position.
        No rounding until conversion to cells for visualization.

        Args:
            duration (float): Duration of movement in seconds
        """
        import logging
        logger = logging.getLogger(__name__)

        # Calculate distance traveled in cm (precise)
        distance_cm = duration * self.config.speed_cm_per_sec
        logger.info(f"Duration: {duration}s, Distance: {distance_cm}cm")

        # Update position in cm based on orientation
        if self._current_orientation == "NORTH":
            self._position_y_cm += distance_cm
        elif self._current_orientation == "SOUTH":
            self._position_y_cm -= distance_cm
        elif self._current_orientation == "EAST":
            self._position_x_cm += distance_cm
        elif self._current_orientation == "WEST":
            self._position_x_cm -= distance_cm

        # Log both cm and cell positions
        cell_x, cell_y = self.get_position()
        logger.info(f"New position: ({self._position_x_cm:.2f}, {self._position_y_cm:.2f})cm = cell ({cell_x}, {cell_y})")

        # Update robot's internal state with cm coordinates
        self.robot.set_position(self._position_x_cm, self._position_y_cm)

    def start_mapping(self, room_name: str, x_cm: float, y_cm: float, orientation: str):
        """
        Start a new mapping session for a room.

        Validates starting position and initializes path recording.

        Args:
            room_name (str): Name of the room to map
            x_cm (float): Starting x-coordinate in cm
            y_cm (float): Starting y-coordinate in cm
            orientation (str): Starting orientation

        Raises:
            ValueError: If first room doesn't start at (0,0) or if starting
                       position is invalid for subsequent rooms
        """
        # Validation: first room must start at (0,0)
        if len(self.world_map.get_room_names()) == 0:
            if x_cm != 0.0 or y_cm != 0.0:
                raise ValueError("First room must start at position (0, 0)")
        else:
            # Subsequent rooms must start in an existing room
            existing_room = self.world_map.get_room_at_position(x_cm, y_cm)
            if existing_room is None:
                raise ValueError(f"Starting position ({x_cm}, {y_cm}) is not in a mapped room")

        # Initialize mapping session
        self._mapping_active = True
        self._current_room_name = room_name
        self._start_position_cm = (x_cm, y_cm)

        # Set robot position
        self.set_position_cm(x_cm, y_cm, orientation)

        # Record initial position
        self._current_path_cm = [(x_cm, y_cm, orientation)]

    def record_movement(self, duration: float):
        """
        Record a forward movement during mapping.

        Updates position and records precise cm position with orientation.

        Args:
            duration (float): Duration of movement in seconds

        Raises:
            RuntimeError: If mapping is not active
        """
        if not self._mapping_active:
            raise RuntimeError("Cannot record movement: mapping session not started")

        # Update position (in cm)
        self.update_position(duration)

        # Record position with orientation
        self._current_path_cm.append((
            self._position_x_cm,
            self._position_y_cm,
            self._current_orientation
        ))

    def _simplify_path_to_corners_cm(self, path: List[Tuple[float, float, str]]) -> List[Point]:
        """
        Simplify a detailed path to only corner points (direction changes).

        A corner is a point where the robot changes direction (orientation changes).
        When we detect an orientation change, we add the PREVIOUS point as a corner
        (the position where the robot was when it turned).

        Args:
            path: Detailed path with all positions (x_cm, y_cm, orientation)

        Returns:
            Simplified path with only corner points as Point objects
        """
        if len(path) < 2:
            return [Point(path[0][0], path[0][1])]

        corners = [Point(path[0][0], path[0][1])]  # Always include start
        last_orientation = path[0][2]

        for i in range(1, len(path)):
            curr_orientation = path[i][2]

            # Corner detected: orientation changed from previous
            if curr_orientation != last_orientation:
                # Add the PREVIOUS point as a corner (where we were when we turned)
                prev_x, prev_y = path[i-1][0], path[i-1][1]

                # Only add if it's different from the last corner (avoid duplicates)
                if len(corners) == 0 or prev_x != corners[-1].x_cm or prev_y != corners[-1].y_cm:
                    corners.append(Point(prev_x, prev_y))

                last_orientation = curr_orientation

        return corners

    def get_current_path(self) -> List[Tuple[float, float, str]]:
        """
        Get the current recorded path in cm coordinates.

        Returns:
            List[Tuple[float, float, str]]: List of (x_cm, y_cm, orientation) tuples
        """
        return self._current_path_cm.copy()

    def clear_path(self):
        """
        Clear the current path and end mapping session.
        """
        self._current_path_cm = []
        self._mapping_active = False
        self._current_room_name = None
        self._start_position_cm = None

    def is_mapping_active(self) -> bool:
        """
        Check if a mapping session is currently active.

        Returns:
            bool: True if mapping is active, False otherwise
        """
        return self._mapping_active

    def is_shape_closed(self, tolerance_cm: float = 30.0) -> bool:
        """
        Check if the traced path forms a closed 2D shape.

        The shape is considered closed if:
        1. Path has at least 4 points (minimum for a 2D shape)
        2. Path covers both X and Y dimensions (not just a straight line)
        3. Current position is aligned with start position (same x OR same y)
        4. Current position is within tolerance_cm of start position

        Args:
            tolerance_cm (float): Maximum distance (in cm) from start to consider closed

        Returns:
            bool: True if shape is closed or nearly closed, False otherwise

        Raises:
            RuntimeError: If mapping is not active
            ValueError: If path is invalid (not aligned, insufficient points, or not 2D)
        """
        if not self._mapping_active:
            raise RuntimeError("Cannot check closure: mapping session not started")

        if self._start_position_cm is None:
            raise RuntimeError("Start position not set")

        # Check minimum path length (at least 4 points for a shape)
        if len(self._current_path_cm) < 4:
            raise ValueError(
                f"Cannot close shape: path has only {len(self._current_path_cm)} points. "
                f"Need at least 4 points to form a 2D shape."
            )

        # Check that path covers both X and Y dimensions (not just a line)
        x_coords = [pos[0] for pos in self._current_path_cm]
        y_coords = [pos[1] for pos in self._current_path_cm]

        # Check if all x values are approximately the same (within 1cm tolerance)
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)

        if x_range < 1.0 or y_range < 1.0:
            raise ValueError(
                "Cannot close shape: path is a straight line. "
                "A valid room must be a 2D shape covering both X and Y dimensions."
            )

        start_x, start_y = self._start_position_cm
        current_x, current_y = self._position_x_cm, self._position_y_cm

        # Check if aligned (same cell column OR same cell row)
        # Convert to cells for alignment check
        start_cell_x = int(start_x // self.config.cell_size_cm)
        start_cell_y = int(start_y // self.config.cell_size_cm)
        current_cell_x = int(current_x // self.config.cell_size_cm)
        current_cell_y = int(current_y // self.config.cell_size_cm)

        is_aligned = (current_cell_x == start_cell_x) or (current_cell_y == start_cell_y)

        if not is_aligned:
            raise ValueError(
                f"Cannot close shape: current position ({current_x:.1f}, {current_y:.1f}) [cell ({current_cell_x}, {current_cell_y})] "
                f"is not aligned with start position ({start_x:.1f}, {start_y:.1f}) [cell ({start_cell_x}, {start_cell_y})]. "
                f"Robot must be in the same row or column (in cells) as the starting point."
            )

        # Calculate Euclidean distance to start
        distance = ((current_x - start_x)**2 + (current_y - start_y)**2)**0.5

        return distance <= tolerance_cm

    def _calculate_auto_complete_path(self) -> Optional[List[Tuple[float, float, str]]]:
        """
        Calculate if the shape can be auto-completed with 1-2 straight lines.

        Returns:
            List of waypoints to complete the path, or None if not possible
            Each waypoint is (x_cm, y_cm, orientation)
        """
        if self._start_position_cm is None:
            return None

        start_x, start_y = self._start_position_cm
        current_x = self._position_x_cm
        current_y = self._position_y_cm

        # Already at start (within 1cm tolerance)
        if abs(current_x - start_x) < 1.0 and abs(current_y - start_y) < 1.0:
            return []

        delta_x = start_x - current_x
        delta_y = start_y - current_y

        completion_path = []

        # Case 1: Aligned horizontally (same y, only need to move in x direction)
        if abs(delta_y) < 1.0:
            # One straight line in x direction
            orientation = "EAST" if delta_x > 0 else "WEST"
            completion_path.append((start_x, start_y, orientation))
            return completion_path

        # Case 2: Aligned vertically (same x, only need to move in y direction)
        if abs(delta_x) < 1.0:
            # One straight line in y direction
            orientation = "NORTH" if delta_y > 0 else "SOUTH"
            completion_path.append((start_x, start_y, orientation))
            return completion_path

        # Case 3: L-shape needed (2 straight lines)
        # Strategy: Determine which axis we were moving on, then check if continuing
        # on that axis moves us toward start. If yes, complete that edge first.
        # If no, complete the perpendicular edge first.

        # Look at the last movement to determine current direction
        was_moving_horizontally = False
        moving_toward_start_on_same_axis = False

        if len(self._current_path_cm) >= 2:
            # Get the previous position
            prev_x, prev_y, _ = self._current_path_cm[-2]

            # Determine if last movement was horizontal or vertical
            dx_last_move = abs(current_x - prev_x)
            dy_last_move = abs(current_y - prev_y)

            was_moving_horizontally = dx_last_move > dy_last_move

            # Check if continuing on same axis moves us toward start
            if was_moving_horizontally:
                # We were moving in X direction
                # Check if we need to continue in same X direction to reach start
                movement_direction_x = current_x - prev_x  # positive = was going east
                needed_direction_x = start_x - current_x    # positive = need to go east
                # If signs match, continuing same axis moves toward start
                moving_toward_start_on_same_axis = (movement_direction_x * needed_direction_x > 0)
            else:
                # We were moving in Y direction
                movement_direction_y = current_y - prev_y
                needed_direction_y = start_y - current_y
                moving_toward_start_on_same_axis = (movement_direction_y * needed_direction_y > 0)
        else:
            # Fallback: use current orientation
            was_moving_horizontally = self._current_orientation in ["EAST", "WEST"]

        # Decide which edge to complete first
        complete_horizontal_first = was_moving_horizontally and moving_toward_start_on_same_axis
        complete_vertical_first = not was_moving_horizontally and moving_toward_start_on_same_axis

        if complete_horizontal_first:
            # Complete horizontal edge first
            corner_x = start_x
            corner_y = current_y
            orientation_horizontal = "EAST" if delta_x > 0 else "WEST"
            completion_path.append((corner_x, corner_y, orientation_horizontal))

            orientation_vertical = "NORTH" if delta_y > 0 else "SOUTH"
            completion_path.append((start_x, start_y, orientation_vertical))
        elif complete_vertical_first:
            # Complete vertical edge first
            corner_x = current_x
            corner_y = start_y
            orientation_vertical = "NORTH" if delta_y > 0 else "SOUTH"
            completion_path.append((corner_x, corner_y, orientation_vertical))

            orientation_horizontal = "EAST" if delta_x > 0 else "WEST"
            completion_path.append((start_x, start_y, orientation_horizontal))
        else:
            # We're moving away from start on current axis, so turn perpendicular first
            if was_moving_horizontally:
                # Turn and go vertical first
                corner_x = current_x
                corner_y = start_y
                orientation_vertical = "NORTH" if delta_y > 0 else "SOUTH"
                completion_path.append((corner_x, corner_y, orientation_vertical))

                orientation_horizontal = "EAST" if delta_x > 0 else "WEST"
                completion_path.append((start_x, start_y, orientation_horizontal))
            else:
                # Turn and go horizontal first
                corner_x = start_x
                corner_y = current_y
                orientation_horizontal = "EAST" if delta_x > 0 else "WEST"
                completion_path.append((corner_x, corner_y, orientation_horizontal))

                orientation_vertical = "NORTH" if delta_y > 0 else "SOUTH"
                completion_path.append((start_x, start_y, orientation_vertical))

        return completion_path

    def save_room(self, tolerance_cm: float = 50.0):
        """
        Save the currently mapped room to the world map.

        This method:
        1. Attempts to auto-complete the shape with 1-2 straight lines
        2. Validates that auto-completion is possible
        3. Adds completion waypoints to the path (including corner points for L-shapes)
        4. Simplifies path to corner points
        5. Creates a Room object and stores it in the world map
        6. Clears the current path and ends the mapping session

        Args:
            tolerance_cm (float): Not used anymore (kept for backwards compatibility)

        Raises:
            RuntimeError: If mapping session is not active
            ValueError: If shape cannot be auto-completed with 1-2 straight lines
        """
        if not self._mapping_active:
            raise RuntimeError("Cannot save room: mapping session not started")

        if self._current_room_name is None:
            raise RuntimeError("Cannot save room: no room name set")

        # Try to calculate auto-complete path
        completion_path = self._calculate_auto_complete_path()

        if completion_path is None:
            raise ValueError("Cannot auto-complete shape: no start position set")

        # Start building the path to save
        path_to_save = self._current_path_cm.copy()

        # Add completion waypoints to the path and update robot position
        if completion_path:
            start_x, start_y = self._start_position_cm
            for waypoint in completion_path:
                x, y, orientation = waypoint
                path_to_save.append((x, y, orientation))

            # Update robot's position to the final waypoint (which should be start)
            final_x, final_y, final_orientation = completion_path[-1]
            self._position_x_cm = final_x
            self._position_y_cm = final_y
            self._current_orientation = final_orientation

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Path to save (cm): {len(path_to_save)} points")

        # Simplify path to corner points only
        boundary_corners = self._simplify_path_to_corners_cm(path_to_save)
        logger.info(f"Boundary corners: {len(boundary_corners)} points")
        logger.info(f"Corner points: {[(p.x_cm, p.y_cm) for p in boundary_corners]}")

        # Create Room object with single polygon
        room = Room(
            name=self._current_room_name,
            polygons=[boundary_corners]
        )

        # Auto-assign edge aliases for easier navigation
        self._auto_assign_edge_aliases(room)

        # Add to world map
        self.world_map.add_room(room)

        # Clear the current path and end mapping session
        self.clear_path()

    def _auto_assign_edge_aliases(self, room: Room):
        """
        Automatically assign aliases to all edges in a room.

        Uses sequential naming: edge_0, edge_1, edge_2, etc.
        Format: edge_<polygon_idx>_<edge_idx> for clarity.

        Args:
            room (Room): The room to assign aliases to
        """
        for poly_idx, polygon in enumerate(room.polygons):
            for edge_idx in range(len(polygon)):
                # Format: edge_0_0, edge_0_1, etc. for polygon 0
                # Format: edge_1_0, edge_1_1, etc. for polygon 1
                alias = f"edge_{poly_idx}_{edge_idx}"
                room.set_edge_alias(poly_idx, edge_idx, alias)

    def navigate_to_edge(self, room_name: str, start_alias: str, end_alias: str) -> List[Tuple[float, float, str]]:
        """
        Generate navigation waypoints from start_alias to end_alias along room perimeter.

        This method finds the shortest path along the room's polygon perimeter between
        two aliased edges. It returns a sequence of waypoints (positions + orientations)
        that the robot can follow.

        Args:
            room_name (str): Name of the room to navigate in
            start_alias (str): Alias of the starting edge
            end_alias (str): Alias of the destination edge

        Returns:
            List[Tuple[float, float, str]]: Navigation waypoints as (x_cm, y_cm, orientation)

        Raises:
            ValueError: If room doesn't exist, aliases not found, or navigation impossible
        """
        # Get the room
        room = self.world_map.get_room(room_name)
        if room is None:
            raise ValueError(f"Room '{room_name}' not found")

        # Find start and end edges
        start_edge = room.find_edge_by_alias(start_alias)
        if start_edge is None:
            raise ValueError(f"Start alias '{start_alias}' not found in room '{room_name}'")

        end_edge = room.find_edge_by_alias(end_alias)
        if end_edge is None:
            raise ValueError(f"End alias '{end_alias}' not found in room '{room_name}'")

        start_poly_idx, start_edge_idx = start_edge
        end_poly_idx, end_edge_idx = end_edge

        # For simplicity, only support navigation within the same polygon
        if start_poly_idx != end_poly_idx:
            raise ValueError(
                f"Navigation between different polygons not yet supported. "
                f"Start edge is in polygon {start_poly_idx}, end edge is in polygon {end_poly_idx}"
            )

        # Get the polygon
        polygon = room.polygons[start_poly_idx]
        n = len(polygon)

        # Calculate paths in both directions (clockwise and counter-clockwise)
        # and choose the shorter one
        if start_edge_idx <= end_edge_idx:
            clockwise_distance = end_edge_idx - start_edge_idx
            counter_clockwise_distance = n - clockwise_distance
        else:
            counter_clockwise_distance = start_edge_idx - end_edge_idx
            clockwise_distance = n - counter_clockwise_distance

        # Choose the shorter path
        if clockwise_distance <= counter_clockwise_distance:
            # Clockwise: start_edge_idx -> end_edge_idx
            waypoints = self._generate_clockwise_path(polygon, start_edge_idx, end_edge_idx)
        else:
            # Counter-clockwise: start_edge_idx -> end_edge_idx (going backwards)
            waypoints = self._generate_counter_clockwise_path(polygon, start_edge_idx, end_edge_idx)

        return waypoints

    def _generate_clockwise_path(
        self,
        polygon: List[Point],
        start_edge_idx: int,
        end_edge_idx: int
    ) -> List[Tuple[float, float, str]]:
        """
        Generate waypoints following polygon edges clockwise.

        Args:
            polygon: The polygon to navigate
            start_edge_idx: Starting edge index
            end_edge_idx: Ending edge index

        Returns:
            List of waypoints (x_cm, y_cm, orientation)
        """
        waypoints = []
        n = len(polygon)

        # Start at the beginning of start_edge
        current_idx = start_edge_idx

        while True:
            point = polygon[current_idx]
            next_idx = (current_idx + 1) % n
            next_point = polygon[next_idx]

            # Calculate orientation for this edge
            orientation = self._calculate_orientation(point, next_point)

            # Add waypoint with current edge orientation
            waypoints.append((point.x_cm, point.y_cm, orientation))

            # Check if we've reached the end edge
            if current_idx == end_edge_idx:
                # For the endpoint, use the orientation of the NEXT edge (after the turn)
                next_next_idx = (next_idx + 1) % n
                next_next_point = polygon[next_next_idx]
                end_orientation = self._calculate_orientation(next_point, next_next_point)
                waypoints.append((next_point.x_cm, next_point.y_cm, end_orientation))
                break

            # Move to next edge
            current_idx = next_idx

        return waypoints

    def _generate_counter_clockwise_path(
        self,
        polygon: List[Point],
        start_edge_idx: int,
        end_edge_idx: int
    ) -> List[Tuple[float, float, str]]:
        """
        Generate waypoints following polygon edges counter-clockwise.

        Args:
            polygon: The polygon to navigate
            start_edge_idx: Starting edge index
            end_edge_idx: Ending edge index

        Returns:
            List of waypoints (x_cm, y_cm, orientation)
        """
        waypoints = []
        n = len(polygon)

        # Start at the beginning of start_edge, but move backwards
        current_idx = start_edge_idx

        while True:
            # For counter-clockwise, we go to the previous point
            point = polygon[current_idx]
            prev_idx = (current_idx - 1) % n
            prev_point = polygon[prev_idx]

            # Orientation is from current point backwards
            orientation = self._calculate_orientation(point, prev_point)

            # Add waypoint
            waypoints.append((point.x_cm, point.y_cm, orientation))

            # Check if we've reached the end edge
            if current_idx == (end_edge_idx + 1) % n:
                # Add the starting point of the end edge (which is the endpoint going backwards)
                end_point = polygon[end_edge_idx]
                waypoints.append((end_point.x_cm, end_point.y_cm, orientation))
                break

            # Move to previous edge
            current_idx = prev_idx

        return waypoints

    def _calculate_orientation(self, from_point: Point, to_point: Point) -> str:
        """
        Calculate orientation (NORTH/SOUTH/EAST/WEST) from one point to another.

        Args:
            from_point: Starting point
            to_point: Ending point

        Returns:
            Orientation string

        Raises:
            ValueError: If movement is not axis-aligned
        """
        dx = to_point.x_cm - from_point.x_cm
        dy = to_point.y_cm - from_point.y_cm

        # Check for axis-aligned movement
        if abs(dx) > 1.0 and abs(dy) > 1.0:
            raise ValueError(
                f"Movement from ({from_point.x_cm}, {from_point.y_cm}) to "
                f"({to_point.x_cm}, {to_point.y_cm}) is not axis-aligned. "
                f"Robot can only move in cardinal directions."
            )

        # Determine primary direction
        if abs(dy) > abs(dx):
            return "NORTH" if dy > 0 else "SOUTH"
        else:
            return "EAST" if dx > 0 else "WEST"
