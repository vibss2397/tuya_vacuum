"""
Polygon Fill Algorithm

Implements scanline-based polygon filling to find all interior cells
of a closed polygon defined by a path of grid coordinates.
"""

from typing import List, Tuple, Set

def fill_polygon(path_points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Fill the interior of a polygon using scanline algorithm + perimeter tracing.
    """
    if len(path_points) < 3:
        raise ValueError("Polygon must have at least 3 points")

    filled_cells: Set[Tuple[int, int]] = set()

    # STEP 1: Trace the Perimeter
    # We explicitly add the outline because scanline with half-open intervals
    # often drops the bottom-most or top-most rows.
    n = len(path_points)
    for i in range(n):
        p1 = path_points[i]
        p2 = path_points[(i + 1) % n]
        _add_line_points(filled_cells, p1, p2)

    # STEP 2: Scanline Fill (Interior)
    y_min = min(p[1] for p in path_points)
    y_max = max(p[1] for p in path_points)

    for y in range(y_min, y_max + 1):
        intersections = _find_intersections(path_points, y)
        intersections.sort()

        # Fill between pairs (standard even-odd parity)
        # Because we use half-open intervals, we will always get an even number of intersections
        for i in range(0, len(intersections), 2):
            if i + 1 < len(intersections):
                x_start = intersections[i]
                x_end = intersections[i + 1]
                
                # Fill the span. We can skip the endpoints (x_start, x_end) 
                # because Step 1 already added them, but adding them again is harmless (Set).
                for x in range(x_start + 1, x_end):
                    filled_cells.add((x, y))

    return sorted(list(filled_cells))


def _find_intersections(vertices: List[Tuple[int, int]], y: int) -> List[int]:
    n = len(vertices)
    intersections = []

    for i in range(n):
        v1 = vertices[i]
        v2 = vertices[(i + 1) % n]
        x1, y1 = v1
        x2, y2 = v2

        # Skip horizontal edges in scanline (handled by perimeter trace)
        if y1 == y2:
            continue

        y_min_edge = min(y1, y2)
        y_max_edge = max(y1, y2)

        # FIXED LOGIC: Half-Open Interval [y_min, y_max)
        # We include the lower Y bound but EXCLUDE the upper Y bound.
        # This ensures that at a vertex shared by two vertical edges, 
        # only the edge starting at that vertex is counted, preserving parity.
        if y_min_edge <= y < y_max_edge:
            # Linear Interpolation
            t = (y - y1) / (y2 - y1)
            x_intersect = x1 + t * (x2 - x1)
            intersections.append(int(round(x_intersect)))

    return intersections


def _add_line_points(filled_cells: Set[Tuple[int, int]], p1: Tuple[int, int], p2: Tuple[int, int]):
    """Helper to add all integer points on a line segment to the set."""
    x1, y1 = p1
    x2, y2 = p2
    
    # Distance for interpolation steps
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    steps = max(dx, dy)
    
    if steps == 0:
        filled_cells.add(p1)
        return

    for i in range(steps + 1):
        t = i / steps
        x = int(round(x1 + t * (x2 - x1)))
        y = int(round(y1 + t * (y2 - y1)))
        filled_cells.add((x, y))