"""
Persistence Module

Handles serialization and deserialization of world maps and configuration.
"""

import json
from typing import Tuple, Dict, Any
from src.cell import WorldMap, Cell
from src.constants import CalibrationConfig


def serialize_map(world_map: WorldMap, config: CalibrationConfig) -> str:
    """
    Serialize a WorldMap and CalibrationConfig to JSON string.

    Args:
        world_map: The WorldMap to serialize
        config: The CalibrationConfig to serialize

    Returns:
        JSON string representation of the map and configuration
    """
    # Build cells data structure
    cells_data = []
    for cell in world_map.get_all_cells():
        cells_data.append({
            "x": cell.x,
            "y": cell.y,
            "room_name": cell.room_name
        })

    # Build complete data structure
    data = {
        "version": "1.0",
        "config": {
            "speed_cm_per_sec": config.speed_cm_per_sec,
            "turn_rate_deg_per_sec": config.turn_rate_deg_per_sec,
            "cell_size_cm": config.cell_size_cm
        },
        "cells": cells_data,
        "rooms": world_map.get_room_names()
    }

    return json.dumps(data, indent=2)


def deserialize_map(json_string: str) -> Tuple[WorldMap, CalibrationConfig]:
    """
    Deserialize a WorldMap and CalibrationConfig from JSON string.

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
    if "cells" not in data:
        raise ValueError("Missing 'cells' field in JSON")

    # Reconstruct CalibrationConfig
    config_data = data["config"]
    config = CalibrationConfig(
        speed_cm_per_sec=config_data.get("speed_cm_per_sec", 10.0),
        turn_rate_deg_per_sec=config_data.get("turn_rate_deg_per_sec", 90.0),
        cell_size_cm=config_data.get("cell_size_cm", 30.0)
    )

    # Reconstruct WorldMap
    world_map = WorldMap()
    for cell_data in data["cells"]:
        world_map.set_cell(
            x=cell_data["x"],
            y=cell_data["y"],
            room_name=cell_data.get("room_name")
        )

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
