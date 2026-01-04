"""
Unit tests for persistence of edge aliases
"""

import unittest
import json
from src.persistence import serialize_map, deserialize_map
from src.room import WorldMap, Room, Point
from src.constants import CalibrationConfig


class TestPersistenceWithAliases(unittest.TestCase):
    """Test cases for serialization/deserialization of edge aliases"""

    def setUp(self):
        """Set up a world map with edge aliases"""
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        self.world_map = WorldMap()

        # Create a room with edge aliases
        polygon = [
            Point(0.0, 0.0),
            Point(60.0, 0.0),
            Point(60.0, 90.0),
            Point(0.0, 90.0)
        ]
        room = Room(name="kitchen", polygons=[polygon])
        room.set_edge_alias(0, 0, "south_wall")
        room.set_edge_alias(0, 1, "east_wall")
        room.set_edge_alias(0, 2, "north_wall")
        room.set_edge_alias(0, 3, "west_wall")

        self.world_map.add_room(room)

    def test_serialize_with_edge_aliases(self):
        """Test serialization of rooms with edge aliases"""
        json_string = serialize_map(self.world_map, self.config)
        data = json.loads(json_string)

        # Verify structure
        self.assertEqual(data["version"], "2.0")
        self.assertEqual(len(data["rooms"]), 1)

        room_data = data["rooms"][0]
        self.assertEqual(room_data["name"], "kitchen")
        self.assertIn("edge_aliases", room_data)

        # Verify edge aliases
        aliases = room_data["edge_aliases"]
        self.assertEqual(len(aliases), 4)

        # Check that all aliases are present
        alias_dict = {
            (a["polygon_idx"], a["edge_idx"]): a["alias"]
            for a in aliases
        }
        self.assertEqual(alias_dict[(0, 0)], "south_wall")
        self.assertEqual(alias_dict[(0, 1)], "east_wall")
        self.assertEqual(alias_dict[(0, 2)], "north_wall")
        self.assertEqual(alias_dict[(0, 3)], "west_wall")

    def test_deserialize_with_edge_aliases(self):
        """Test deserialization of rooms with edge aliases"""
        # Serialize first
        json_string = serialize_map(self.world_map, self.config)

        # Deserialize
        restored_map, restored_config = deserialize_map(json_string)

        # Verify room was restored
        room = restored_map.get_room("kitchen")
        self.assertIsNotNone(room)

        # Verify edge aliases were restored
        self.assertEqual(room.get_edge_alias(0, 0), "south_wall")
        self.assertEqual(room.get_edge_alias(0, 1), "east_wall")
        self.assertEqual(room.get_edge_alias(0, 2), "north_wall")
        self.assertEqual(room.get_edge_alias(0, 3), "west_wall")

    def test_serialize_without_edge_aliases(self):
        """Test serialization of rooms without edge aliases"""
        # Create a room without aliases
        world_map = WorldMap()
        polygon = [
            Point(0.0, 0.0),
            Point(60.0, 0.0),
            Point(60.0, 90.0),
            Point(0.0, 90.0)
        ]
        room = Room(name="bedroom", polygons=[polygon])
        world_map.add_room(room)

        json_string = serialize_map(world_map, self.config)
        data = json.loads(json_string)

        # Verify edge_aliases is not in JSON (to keep it clean)
        room_data = data["rooms"][0]
        self.assertNotIn("edge_aliases", room_data)

    def test_deserialize_without_edge_aliases(self):
        """Test deserialization of rooms without edge aliases (backward compatibility)"""
        # Create JSON without edge_aliases field
        json_data = {
            "version": "2.0",
            "config": {
                "speed_cm_per_sec": 10.0,
                "turn_rate_deg_per_sec": 90.0,
                "cell_size_cm": 30.0
            },
            "rooms": [
                {
                    "name": "bedroom",
                    "polygons": [
                        [
                            {"x_cm": 0.0, "y_cm": 0.0},
                            {"x_cm": 60.0, "y_cm": 0.0},
                            {"x_cm": 60.0, "y_cm": 90.0},
                            {"x_cm": 0.0, "y_cm": 90.0}
                        ]
                    ]
                }
            ]
        }

        json_string = json.dumps(json_data)
        world_map, config = deserialize_map(json_string)

        # Verify room was loaded
        room = world_map.get_room("bedroom")
        self.assertIsNotNone(room)

        # Verify edge_aliases is empty
        self.assertEqual(len(room.edge_aliases), 0)

    def test_roundtrip_with_multiple_rooms(self):
        """Test serialization and deserialization with multiple rooms"""
        # Add another room
        polygon2 = [
            Point(100.0, 0.0),
            Point(150.0, 0.0),
            Point(150.0, 50.0),
            Point(100.0, 50.0)
        ]
        room2 = Room(name="bathroom", polygons=[polygon2])
        room2.set_edge_alias(0, 0, "bath_south")
        room2.set_edge_alias(0, 1, "bath_east")
        self.world_map.add_room(room2)

        # Serialize and deserialize
        json_string = serialize_map(self.world_map, self.config)
        restored_map, restored_config = deserialize_map(json_string)

        # Verify both rooms
        kitchen = restored_map.get_room("kitchen")
        self.assertEqual(kitchen.get_edge_alias(0, 0), "south_wall")
        self.assertEqual(kitchen.get_edge_alias(0, 1), "east_wall")

        bathroom = restored_map.get_room("bathroom")
        self.assertEqual(bathroom.get_edge_alias(0, 0), "bath_south")
        self.assertEqual(bathroom.get_edge_alias(0, 1), "bath_east")

    def test_alias_lookup_after_deserialization(self):
        """Test that alias lookup works after deserialization"""
        # Serialize and deserialize
        json_string = serialize_map(self.world_map, self.config)
        restored_map, _ = deserialize_map(json_string)

        # Test find_edge_by_alias
        room = restored_map.get_room("kitchen")
        self.assertEqual(room.find_edge_by_alias("south_wall"), (0, 0))
        self.assertEqual(room.find_edge_by_alias("east_wall"), (0, 1))
        self.assertEqual(room.find_edge_by_alias("north_wall"), (0, 2))
        self.assertEqual(room.find_edge_by_alias("west_wall"), (0, 3))


if __name__ == "__main__":
    unittest.main()
