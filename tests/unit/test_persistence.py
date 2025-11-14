"""
Unit tests for Persistence module
"""

import unittest
import json
import os
import tempfile
from src.persistence import serialize_map, deserialize_map, save_to_file, load_from_file
from src.cell import WorldMap
from src.constants import CalibrationConfig


class TestSerialization(unittest.TestCase):
    """Test cases for map serialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.world_map = WorldMap()
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )

    def test_serialize_empty_map(self):
        """Test serializing an empty map"""
        json_string = serialize_map(self.world_map, self.config)
        data = json.loads(json_string)

        # Verify structure
        self.assertIn("version", data)
        self.assertIn("config", data)
        self.assertIn("cells", data)
        self.assertIn("rooms", data)

        # Verify empty map
        self.assertEqual(len(data["cells"]), 0)
        self.assertEqual(len(data["rooms"]), 0)

    def test_serialize_map_with_single_room(self):
        """Test serializing a map with one room"""
        # Add cells for a simple room
        self.world_map.set_cell(0, 0, "kitchen")
        self.world_map.set_cell(0, 1, "kitchen")
        self.world_map.set_cell(1, 0, "kitchen")
        self.world_map.set_cell(1, 1, "kitchen")

        json_string = serialize_map(self.world_map, self.config)
        data = json.loads(json_string)

        # Verify cells
        self.assertEqual(len(data["cells"]), 4)
        self.assertEqual(len(data["rooms"]), 1)
        self.assertIn("kitchen", data["rooms"])

        # Verify cell structure
        for cell in data["cells"]:
            self.assertIn("x", cell)
            self.assertIn("y", cell)
            self.assertIn("room_name", cell)
            self.assertEqual(cell["room_name"], "kitchen")

    def test_serialize_map_with_multiple_rooms(self):
        """Test serializing a map with multiple rooms"""
        # Add two rooms
        self.world_map.set_cell(0, 0, "bedroom")
        self.world_map.set_cell(0, 1, "bedroom")
        self.world_map.set_cell(2, 0, "bathroom")
        self.world_map.set_cell(2, 1, "bathroom")

        json_string = serialize_map(self.world_map, self.config)
        data = json.loads(json_string)

        # Verify multiple rooms
        self.assertEqual(len(data["cells"]), 4)
        self.assertEqual(len(data["rooms"]), 2)
        self.assertIn("bedroom", data["rooms"])
        self.assertIn("bathroom", data["rooms"])

    def test_serialize_config_values(self):
        """Test that config values are correctly serialized"""
        json_string = serialize_map(self.world_map, self.config)
        data = json.loads(json_string)

        config_data = data["config"]
        self.assertEqual(config_data["speed_cm_per_sec"], 10.0)
        self.assertEqual(config_data["turn_rate_deg_per_sec"], 90.0)
        self.assertEqual(config_data["cell_size_cm"], 30.0)

    def test_serialize_negative_coordinates(self):
        """Test serializing cells with negative coordinates"""
        self.world_map.set_cell(-1, -1, "room")
        self.world_map.set_cell(-2, 0, "room")

        json_string = serialize_map(self.world_map, self.config)
        data = json.loads(json_string)

        # Verify negative coordinates preserved
        cells = {(c["x"], c["y"]) for c in data["cells"]}
        self.assertIn((-1, -1), cells)
        self.assertIn((-2, 0), cells)


class TestDeserialization(unittest.TestCase):
    """Test cases for map deserialization"""

    def test_deserialize_empty_map(self):
        """Test deserializing an empty map"""
        json_string = json.dumps({
            "version": "1.0",
            "config": {
                "speed_cm_per_sec": 10.0,
                "turn_rate_deg_per_sec": 90.0,
                "cell_size_cm": 30.0
            },
            "cells": [],
            "rooms": []
        })

        world_map, config = deserialize_map(json_string)

        # Verify empty map
        self.assertEqual(len(world_map.get_all_cells()), 0)
        self.assertEqual(len(world_map.get_room_names()), 0)

        # Verify config
        self.assertEqual(config.speed_cm_per_sec, 10.0)
        self.assertEqual(config.turn_rate_deg_per_sec, 90.0)
        self.assertEqual(config.cell_size_cm, 30.0)

    def test_deserialize_map_with_cells(self):
        """Test deserializing a map with cells"""
        json_string = json.dumps({
            "version": "1.0",
            "config": {
                "speed_cm_per_sec": 15.0,
                "turn_rate_deg_per_sec": 120.0,
                "cell_size_cm": 25.0
            },
            "cells": [
                {"x": 0, "y": 0, "room_name": "living_room"},
                {"x": 0, "y": 1, "room_name": "living_room"},
                {"x": 1, "y": 0, "room_name": "living_room"}
            ],
            "rooms": ["living_room"]
        })

        world_map, config = deserialize_map(json_string)

        # Verify cells
        self.assertEqual(len(world_map.get_all_cells()), 3)
        living_room_cells = world_map.get_all_cells_for_room("living_room")
        self.assertEqual(len(living_room_cells), 3)

        # Verify specific cells exist
        self.assertTrue(world_map.cell_exists(0, 0))
        self.assertTrue(world_map.cell_exists(0, 1))
        self.assertTrue(world_map.cell_exists(1, 0))

        # Verify config
        self.assertEqual(config.speed_cm_per_sec, 15.0)

    def test_deserialize_invalid_json(self):
        """Test that invalid JSON raises ValueError"""
        invalid_json = "{ invalid json }"

        with self.assertRaises(ValueError) as context:
            deserialize_map(invalid_json)

        self.assertIn("Invalid JSON", str(context.exception))

    def test_deserialize_missing_config_field(self):
        """Test that missing config field raises ValueError"""
        json_string = json.dumps({
            "version": "1.0",
            "cells": []
        })

        with self.assertRaises(ValueError) as context:
            deserialize_map(json_string)

        self.assertIn("config", str(context.exception))

    def test_deserialize_missing_cells_field(self):
        """Test that missing cells field raises ValueError"""
        json_string = json.dumps({
            "version": "1.0",
            "config": {
                "speed_cm_per_sec": 10.0,
                "turn_rate_deg_per_sec": 90.0,
                "cell_size_cm": 30.0
            }
        })

        with self.assertRaises(ValueError) as context:
            deserialize_map(json_string)

        self.assertIn("cells", str(context.exception))

    def test_deserialize_negative_coordinates(self):
        """Test deserializing cells with negative coordinates"""
        json_string = json.dumps({
            "version": "1.0",
            "config": {
                "speed_cm_per_sec": 10.0,
                "turn_rate_deg_per_sec": 90.0,
                "cell_size_cm": 30.0
            },
            "cells": [
                {"x": -1, "y": -2, "room_name": "room"},
                {"x": 0, "y": -1, "room_name": "room"}
            ],
            "rooms": ["room"]
        })

        world_map, config = deserialize_map(json_string)

        # Verify negative coordinates
        self.assertTrue(world_map.cell_exists(-1, -2))
        self.assertTrue(world_map.cell_exists(0, -1))


class TestRoundTrip(unittest.TestCase):
    """Test cases for serialize-deserialize round trips"""

    def test_round_trip_preserves_data(self):
        """Test that serialize then deserialize preserves all data"""
        # Create original map
        original_map = WorldMap()
        original_map.set_cell(0, 0, "room1")
        original_map.set_cell(0, 1, "room1")
        original_map.set_cell(1, 0, "room2")

        original_config = CalibrationConfig(
            speed_cm_per_sec=12.5,
            turn_rate_deg_per_sec=85.0,
            cell_size_cm=35.0
        )

        # Serialize then deserialize
        json_string = serialize_map(original_map, original_config)
        restored_map, restored_config = deserialize_map(json_string)

        # Verify maps are identical
        original_cells = set((c.x, c.y, c.room_name) for c in original_map.get_all_cells())
        restored_cells = set((c.x, c.y, c.room_name) for c in restored_map.get_all_cells())
        self.assertEqual(original_cells, restored_cells)

        # Verify configs are identical
        self.assertEqual(restored_config.speed_cm_per_sec, original_config.speed_cm_per_sec)
        self.assertEqual(restored_config.turn_rate_deg_per_sec, original_config.turn_rate_deg_per_sec)
        self.assertEqual(restored_config.cell_size_cm, original_config.cell_size_cm)


class TestFileOperations(unittest.TestCase):
    """Test cases for file save/load operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_map.json")

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def test_save_to_file(self):
        """Test saving map to file"""
        world_map = WorldMap()
        world_map.set_cell(0, 0, "kitchen")
        config = CalibrationConfig(speed_cm_per_sec=10.0, cell_size_cm=30.0)

        # Save to file
        save_to_file(world_map, config, self.test_file)

        # Verify file exists and contains valid JSON
        self.assertTrue(os.path.exists(self.test_file))

        with open(self.test_file, 'r') as f:
            data = json.load(f)

        self.assertIn("cells", data)
        self.assertIn("config", data)

    def test_load_from_file(self):
        """Test loading map from file"""
        # Create a test file
        test_data = {
            "version": "1.0",
            "config": {
                "speed_cm_per_sec": 10.0,
                "turn_rate_deg_per_sec": 90.0,
                "cell_size_cm": 30.0
            },
            "cells": [
                {"x": 0, "y": 0, "room_name": "bedroom"}
            ],
            "rooms": ["bedroom"]
        }

        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)

        # Load from file
        world_map, config = load_from_file(self.test_file)

        # Verify loaded data
        self.assertEqual(len(world_map.get_all_cells()), 1)
        self.assertTrue(world_map.cell_exists(0, 0))
        self.assertEqual(config.speed_cm_per_sec, 10.0)

    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file raises error"""
        nonexistent_file = os.path.join(self.temp_dir, "does_not_exist.json")

        with self.assertRaises(FileNotFoundError):
            load_from_file(nonexistent_file)

    def test_save_and_load_round_trip(self):
        """Test save then load preserves data"""
        # Create original data
        original_map = WorldMap()
        original_map.set_cell(0, 0, "room1")
        original_map.set_cell(1, 1, "room2")
        original_config = CalibrationConfig(
            speed_cm_per_sec=15.0,
            cell_size_cm=25.0
        )

        # Save to file
        save_to_file(original_map, original_config, self.test_file)

        # Load from file
        loaded_map, loaded_config = load_from_file(self.test_file)

        # Verify data preserved
        self.assertEqual(len(loaded_map.get_all_cells()), 2)
        self.assertTrue(loaded_map.cell_exists(0, 0))
        self.assertTrue(loaded_map.cell_exists(1, 1))
        self.assertEqual(loaded_config.speed_cm_per_sec, 15.0)


if __name__ == "__main__":
    unittest.main()
