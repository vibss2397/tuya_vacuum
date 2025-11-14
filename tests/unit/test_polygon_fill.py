"""
Unit tests for polygon fill algorithm
"""

import unittest
from src.polygon_fill import fill_polygon


class TestPolygonFill(unittest.TestCase):
    """Test cases for polygon fill algorithm"""

    def test_simple_rectangle(self):
        """Test filling a simple rectangle"""
        # 2x2 rectangle from (0,0) to (2,2)
        path = [(0, 0), (0, 2), (2, 2), (2, 0)]

        filled = fill_polygon(path)

        # Should contain all 9 cells in the 3x3 grid
        expected = [
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
            (2, 0), (2, 1), (2, 2),
        ]
        self.assertEqual(filled, expected)

    def test_unit_square(self):
        """Test filling a 1x1 square"""
        # 1x1 square
        path = [(0, 0), (0, 1), (1, 1), (1, 0)]

        filled = fill_polygon(path)

        # Should contain all 4 corners
        expected = [(0, 0), (0, 1), (1, 0), (1, 1)]
        self.assertEqual(filled, expected)

    def test_l_shape(self):
        """Test filling an L-shaped polygon"""
        # L-shape
        path = [
            (0, 0), (0, 2),
            (1, 2), (1, 1),
            (2, 1), (2, 0)
        ]

        filled = fill_polygon(path)

        # L-shape interior
        expected = [
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
            (2, 0), (2, 1),
        ]
        self.assertEqual(filled, expected)

    def test_triangle(self):
        """Test filling a triangular polygon"""
        # Triangle with base at y=0
        path = [(0, 0), (2, 0), (1, 2)]

        filled = fill_polygon(path)

        # Triangle should be filled
        # Note: exact cells depend on rasterization
        self.assertIn((0, 0), filled)
        self.assertIn((2, 0), filled)
        self.assertIn((1, 2), filled)
        self.assertIn((1, 1), filled)  # Interior point

    def test_large_rectangle(self):
        """Test filling a larger rectangle"""
        # 3x5 rectangle
        path = [(0, 0), (0, 5), (3, 5), (3, 0)]

        filled = fill_polygon(path)

        # Should have 4 * 6 = 24 cells
        self.assertEqual(len(filled), 24)

        # Check corners
        self.assertIn((0, 0), filled)
        self.assertIn((0, 5), filled)
        self.assertIn((3, 5), filled)
        self.assertIn((3, 0), filled)

        # Check interior
        self.assertIn((1, 2), filled)
        self.assertIn((2, 3), filled)

    def test_invalid_polygon_raises_error(self):
        """Test that polygon with < 3 points raises error"""
        with self.assertRaises(ValueError):
            fill_polygon([(0, 0), (1, 1)])

    def test_negative_coordinates(self):
        """Test polygon with negative coordinates"""
        # Rectangle in negative space
        path = [(-2, -2), (-2, 0), (0, 0), (0, -2)]

        filled = fill_polygon(path)

        # Should contain all cells
        self.assertIn((-2, -2), filled)
        self.assertIn((0, 0), filled)
        self.assertIn((-1, -1), filled)  # Interior point


if __name__ == "__main__":
    unittest.main()
