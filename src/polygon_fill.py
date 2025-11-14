"""
Polygon Fill Algorithm

Implements scanline-based polygon filling to find all interior cells
of a closed polygon defined by a path of grid coordinates.
"""

from typing import List, Tuple, Set


def fill_polygon(path_points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Fill the interior of a polygon using scanline algorithm.

    Given a list of vertex points forming a closed polygon, this function
    returns all grid cells that are inside the polygon (including the perimeter).

    The algorithm works by:
    1. For each y-coordinate (scanline) in the polygon's range
    2. Find all intersections with polygon edges
    3. Fill cells between pairs of intersections (inside-outside pattern)

    Args:
        path_points: List of (x, y) coordinates forming the polygon vertices

    Returns:
        List of (x, y) coordinates for all cells inside and on the polygon

    Raises:
        ValueError: If path has fewer than 3 points
    """
    if len(path_points) < 3:
        raise ValueError("Polygon must have at least 3 points")

    filled_cells: Set[Tuple[int, int]] = set()

    # Find y-coordinate range
    y_min = min(p[1] for p in path_points)
    y_max = max(p[1] for p in path_points)

    # Process each scanline
    for y in range(y_min, y_max + 1):
        # Find intersections with polygon edges at this y
        intersections = _find_intersections(path_points, y)

        if not intersections:
            continue

        # Sort intersections by x-coordinate
        intersections.sort()

        # Fill between pairs of intersections
        i = 0
        while i < len(intersections):
            if i + 1 < len(intersections):
                x_start = intersections[i]
                x_end = intersections[i + 1]

                # Fill all cells from x_start to x_end (inclusive)
                for x in range(x_start, x_end + 1):
                    filled_cells.add((x, y))

                i += 2
            else:
                # Odd number of intersections - add the last point
                filled_cells.add((intersections[i], y))
                i += 1

    return sorted(list(filled_cells))


def _find_intersections(vertices: List[Tuple[int, int]], y: int) -> List[int]:
    """
    Find x-coordinates where polygon edges intersect with a horizontal scanline at y.

    Uses edge-intersection logic with proper handling of horizontal edges and vertices.

    Args:
        vertices: List of polygon vertices
        y: Y-coordinate of the scanline

    Returns:
        List of x-coordinates where edges intersect the scanline
    """
    n = len(vertices)
    intersections = []

    # Process all edges
    for i in range(n):
        v1 = vertices[i]
        v2 = vertices[(i + 1) % n]
        x1, y1 = v1
        x2, y2 = v2

        # Skip horizontal edges (they don't contribute to intersection count)
        if y1 == y2:
            continue

        # Determine edge y-bounds
        y_start = min(y1, y2)
        y_end = max(y1, y2)

        # Check if scanline intersects edge (include both endpoints)
        if y_start <= y <= y_end:
            # Calculate x intersection using linear interpolation
            t = (y - y1) / (y2 - y1)
            x_intersect = x1 + t * (x2 - x1)
            intersections.append(int(round(x_intersect)))

    return intersections
