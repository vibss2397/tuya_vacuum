"""
Persistence Module

Handles serialization and deserialization of world maps and configuration.
"""

import json
from typing import Tuple, Dict, Any
from src.room import WorldMap, Room, Point
from src.constants import CalibrationConfig


def serialize_map(world_map: WorldMap, config: CalibrationConfig) -> str:
    """
    Serialize a WorldMap and CalibrationConfig to JSON string (v2.0 format).

    Args:
        world_map: The WorldMap to serialize
        config: The CalibrationConfig to serialize

    Returns:
        JSON string representation of the map and configuration
    """
    # Build rooms data structure
    rooms_data = []
    for room in world_map.get_all_rooms():
        polygons_data = [
            [{"x_cm": p.x_cm, "y_cm": p.y_cm} for p in polygon]
            for polygon in room.polygons
        ]

        # Serialize edge aliases as list of {polygon_idx, edge_idx, alias}
        edge_aliases_data = [
            {
                "polygon_idx": poly_idx,
                "edge_idx": edge_idx,
                "alias": alias
            }
            for (poly_idx, edge_idx), alias in room.edge_aliases.items()
        ]

        room_data = {
            "name": room.name,
            "polygons": polygons_data
        }

        # Only include edge_aliases if there are any
        if edge_aliases_data:
            room_data["edge_aliases"] = edge_aliases_data

        rooms_data.append(room_data)

    # Build complete data structure
    data = {
        "version": "2.0",
        "config": {
            "speed_cm_per_sec": config.speed_cm_per_sec,
            "turn_rate_deg_per_sec": config.turn_rate_deg_per_sec,
            "cell_size_cm": config.cell_size_cm
        },
        "rooms": rooms_data
    }

    return json.dumps(data, indent=2)


def deserialize_map(json_string: str) -> Tuple[WorldMap, CalibrationConfig]:
    """
    Deserialize a WorldMap and CalibrationConfig from JSON string.
    Supports both v1.0 (cell-based) and v2.0 (cm-based) formats.

    Args:
        json_string: JSON string to deserialize

    Returns:
        Tuple of (WorldMap, CalibrationConfig)

    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    # Validate required fields
    if "config" not in data:
        raise ValueError("Missing 'config' field in JSON")

    # Reconstruct CalibrationConfig
    config_data = data["config"]
    config = CalibrationConfig(
        speed_cm_per_sec=config_data.get("speed_cm_per_sec", 10.0),
        turn_rate_deg_per_sec=config_data.get("turn_rate_deg_per_sec", 90.0),
        cell_size_cm=config_data.get("cell_size_cm", 30.0)
    )

    # Reconstruct WorldMap based on version
    world_map = WorldMap()
    version = data.get("version", "1.0")

    if version == "2.0":
        # New format: rooms with polygons in cm
        if "rooms" not in data:
            raise ValueError("Missing 'rooms' field in v2.0 JSON")

        for room_data in data["rooms"]:
            polygons = [
                [Point(p["x_cm"], p["y_cm"]) for p in polygon_data]
                for polygon_data in room_data["polygons"]
            ]

            # Deserialize edge aliases if present
            edge_aliases = {}
            if "edge_aliases" in room_data:
                for alias_data in room_data["edge_aliases"]:
                    key = (alias_data["polygon_idx"], alias_data["edge_idx"])
                    edge_aliases[key] = alias_data["alias"]

            room = Room(
                name=room_data["name"],
                polygons=polygons,
                edge_aliases=edge_aliases
            )
            world_map.add_room(room)

    elif version == "1.0":
        # Old format: cells and waypoints
        # For now, raise an error - migration can be added later if needed
        raise ValueError(
            "v1.0 format (cell-based) is no longer supported. "
            "Please remap rooms using v2.0 format (cm-based)."
        )

    else:
        raise ValueError(f"Unsupported version: {version}")

    return world_map, config


def save_to_file(world_map: WorldMap, config: CalibrationConfig, filepath: str):
    """
    Save WorldMap and CalibrationConfig to a JSON file.

    Args:
        world_map: The WorldMap to save
        config: The CalibrationConfig to save
        filepath: Path to the output file

    Raises:
        IOError: If file cannot be written
    """
    json_string = serialize_map(world_map, config)

    try:
        with open(filepath, 'w') as f:
            f.write(json_string)
    except IOError as e:
        raise IOError(f"Failed to write to file {filepath}: {e}")


def load_from_file(filepath: str) -> Tuple[WorldMap, CalibrationConfig]:
    """
    Load WorldMap and CalibrationConfig from a JSON file.

    Args:
        filepath: Path to the input file

    Returns:
        Tuple of (WorldMap, CalibrationConfig)

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file contains invalid JSON or data
    """
    try:
        with open(filepath, 'r') as f:
            json_string = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except IOError as e:
        raise IOError(f"Failed to read file {filepath}: {e}")

    return deserialize_map(json_string)
