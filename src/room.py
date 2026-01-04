"""
Room and World Map Data Structures

Manages rooms defined in cm coordinates (not grid cells).
Grid cells are computed on-the-fly for visualization only.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class Point:
    """A point in cm coordinates."""
    x_cm: float
    y_cm: float


@dataclass
class Room:
    """
    A room defined by one or more polygons in cm coordinates.

    For simple rooms: single polygon (list of corner points)
    For complex rooms (L-shapes, obstacles): multiple polygons stitched together

    Attributes:
        name (str): Room name (e.g., "kitchen")
        polygons (List[List[Point]]): List of polygons, where each polygon is a list of Points
        edge_aliases (Dict[Tuple[int, int], str]): Maps (polygon_idx, edge_idx) to alias string
    """
    name: str
    polygons: List[List[Point]] = field(default_factory=list)
    edge_aliases: Dict[Tuple[int, int], str] = field(default_factory=dict)

    def get_all_boundary_points(self) -> List[Point]:
        """
        Get all boundary points from all polygons.

        Returns:
            List[Point]: All boundary points across all polygons
        """
        points = []
        for polygon in self.polygons:
            points.extend(polygon)
        return points

    def set_edge_alias(self, polygon_idx: int, edge_idx: int, alias: str):
        """
        Assign an alias to a polygon edge.

        Args:
            polygon_idx (int): Index of the polygon (0-based)
            edge_idx (int): Index of the edge within polygon (0-based)
            alias (str): Alias string identifier

        Raises:
            ValueError: If polygon_idx or edge_idx is invalid
        """
        if polygon_idx < 0 or polygon_idx >= len(self.polygons):
            raise ValueError(f"Invalid polygon_idx: {polygon_idx}")

        polygon = self.polygons[polygon_idx]
        if edge_idx < 0 or edge_idx >= len(polygon):
            raise ValueError(f"Invalid edge_idx: {edge_idx}")

        self.edge_aliases[(polygon_idx, edge_idx)] = alias

    def get_edge_alias(self, polygon_idx: int, edge_idx: int) -> Optional[str]:
        """
        Get the alias for a polygon edge.

        Args:
            polygon_idx (int): Index of the polygon
            edge_idx (int): Index of the edge within polygon

        Returns:
            Optional[str]: Alias string or None if no alias assigned
        """
        return self.edge_aliases.get((polygon_idx, edge_idx))

    def find_edge_by_alias(self, alias: str) -> Optional[Tuple[int, int]]:
        """
        Find the polygon and edge indices for a given alias.

        Args:
            alias (str): Alias to search for

        Returns:
            Optional[Tuple[int, int]]: (polygon_idx, edge_idx) or None if not found
        """
        for (poly_idx, edge_idx), edge_alias in self.edge_aliases.items():
            if edge_alias == alias:
                return (poly_idx, edge_idx)
        return None

    def get_edge_points(self, polygon_idx: int, edge_idx: int) -> Tuple[Point, Point]:
        """
        Get the two points that define an edge.

        Args:
            polygon_idx (int): Index of the polygon
            edge_idx (int): Index of the edge within polygon

        Returns:
            Tuple[Point, Point]: (start_point, end_point) of the edge

        Raises:
            ValueError: If indices are invalid
        """
        if polygon_idx < 0 or polygon_idx >= len(self.polygons):
            raise ValueError(f"Invalid polygon_idx: {polygon_idx}")

        polygon = self.polygons[polygon_idx]
        if edge_idx < 0 or edge_idx >= len(polygon):
            raise ValueError(f"Invalid edge_idx: {edge_idx}")

        start_point = polygon[edge_idx]
        end_point = polygon[(edge_idx + 1) % len(polygon)]
        return (start_point, end_point)


class WorldMap:
    """
    Manages the world map with rooms stored in cm coordinates.

    Grid cells are computed on-the-fly for visualization only.
    """

    def __init__(self):
        """Initialize an empty world map."""
        self._rooms: Dict[str, Room] = {}

    def add_room(self, room: Room):
        """
        Add or update a room in the map.

        Args:
            room (Room): The room to add
        """
        self._rooms[room.name] = room

    def get_room(self, name: str) -> Optional[Room]:
        """
        Get a room by name.

        Args:
            name (str): Room name

        Returns:
            Optional[Room]: The room, or None if not found
        """
        return self._rooms.get(name)

    def get_all_rooms(self) -> List[Room]:
        """
        Get all rooms.

        Returns:
            List[Room]: List of all rooms
        """
        return list(self._rooms.values())

    def get_room_names(self) -> List[str]:
        """
        Get sorted list of all room names.

        Returns:
            List[str]: Sorted list of room names
        """
        return sorted(self._rooms.keys())

    def room_exists(self, name: str) -> bool:
        """
        Check if a room exists.

        Args:
            name (str): Room name

        Returns:
            bool: True if room exists, False otherwise
        """
        return name in self._rooms

    def add_polygon_to_room(self, room_name: str, polygon: List[Point]):
        """
        Add a polygon to an existing room (for stitching).
        Creates room if it doesn't exist.

        Args:
            room_name (str): Name of the room
            polygon (List[Point]): Polygon to add (list of corner points)
        """
        if room_name in self._rooms:
            self._rooms[room_name].polygons.append(polygon)
        else:
            self._rooms[room_name] = Room(name=room_name, polygons=[polygon])

    def get_room_at_position(self, x_cm: float, y_cm: float) -> Optional[str]:
        """
        Find which room contains the given cm position.
        Uses point-in-polygon test on all rooms.

        Args:
            x_cm (float): X coordinate in cm
            y_cm (float): Y coordinate in cm

        Returns:
            Optional[str]: Room name or None if position is not in any room
        """
        for room in self._rooms.values():
            if self._point_in_room(x_cm, y_cm, room):
                return room.name
        return None

    def _point_in_room(self, x_cm: float, y_cm: float, room: Room) -> bool:
        """
        Check if point is inside any of the room's polygons.

        Args:
            x_cm (float): X coordinate in cm
            y_cm (float): Y coordinate in cm
            room (Room): The room to check

        Returns:
            bool: True if point is in room, False otherwise
        """
        for polygon in room.polygons:
            if self._point_in_polygon(x_cm, y_cm, polygon):
                return True
        return False

    def _point_in_polygon(self, x: float, y: float, polygon: List[Point]) -> bool:
        """
        Ray casting algorithm for point-in-polygon test.

        Casts a horizontal ray from the point to infinity and counts intersections.
        Odd count = inside, even count = outside.

        Args:
            x (float): X coordinate
            y (float): Y coordinate
            polygon (List[Point]): Polygon vertices

        Returns:
            bool: True if point is inside polygon, False otherwise
        """
        if len(polygon) < 3:
            return False

        inside = False
        n = len(polygon)

        p1 = polygon[0]
        for i in range(1, n + 1):
            p2 = polygon[i % n]

            # Check if point is on horizontal edge
            if y == p1.y_cm and p1.y_cm == p2.y_cm:
                if min(p1.x_cm, p2.x_cm) <= x <= max(p1.x_cm, p2.x_cm):
                    return True

            # Check for intersection with horizontal ray
            if y > min(p1.y_cm, p2.y_cm) and y <= max(p1.y_cm, p2.y_cm):
                if x <= max(p1.x_cm, p2.x_cm):
                    if p1.y_cm != p2.y_cm:
                        x_intersection = (y - p1.y_cm) * (p2.x_cm - p1.x_cm) / (p2.y_cm - p1.y_cm) + p1.x_cm
                        if p1.x_cm == p2.x_cm or x <= x_intersection:
                            inside = not inside

            p1 = p2

        return inside
