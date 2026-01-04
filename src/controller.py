"""
Controller Module

Handles user input, command parsing, and mode management.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time


class Mode(Enum):
    """Controller modes"""
    COMMAND_MODE = "COMMAND"
    MAPPING_MODE = "MAPPING"


@dataclass
class ParsedCommand:
    """Represents a parsed command with its parameters"""
    command: str
    params: Dict[str, Any]


class Controller:
    """
    The Controller manages user input and coordinates between command mode
    and mapping mode.

    In command mode, it parses text commands.
    In mapping mode, it handles keyboard inputs for robot control.
    """

    def __init__(self, brain=None):
        """
        Initialize the Controller in command mode.

        Args:
            brain: Optional Brain instance for command execution.
                   If None, controller operates in parse-only mode.
        """
        self._mode = Mode.COMMAND_MODE
        self._brain = brain

        # Key press tracking for duration measurement
        self._key_press_start_time: Optional[float] = None
        self._current_key: Optional[str] = None

    def get_mode(self) -> Mode:
        """
        Get the current mode.

        Returns:
            Mode: Current mode (COMMAND_MODE or MAPPING_MODE)
        """
        return self._mode

    def enter_command_mode(self):
        """Switch to command mode."""
        self._mode = Mode.COMMAND_MODE

    def enter_mapping_mode(self):
        """Switch to mapping mode."""
        self._mode = Mode.MAPPING_MODE

    def parse_command(self, command_string: str) -> ParsedCommand:
        """
        Parse a command string and return structured command object.

        Supported commands:
        - :start <room_name> <x> <y> <orientation>
        - :save
        - :resume
        - :goto <room_name> <start_alias> <end_alias>
        - :alias <room_name> <polygon_idx> <edge_idx> <alias>

        Args:
            command_string: The command string to parse

        Returns:
            ParsedCommand: Structured command with parameters

        Raises:
            ValueError: If command syntax is invalid
        """
        # Strip whitespace and ensure it starts with :
        command_string = command_string.strip()

        if not command_string:
            raise ValueError("Empty command")

        if not command_string.startswith(":"):
            raise ValueError("Commands must start with ':'")

        # Split into parts
        parts = command_string[1:].split()

        if not parts:
            raise ValueError("Empty command after ':'")

        command_name = parts[0].lower()

        # Parse based on command type
        if command_name == "start":
            return self._parse_start_command(parts)
        elif command_name == "save":
            return self._parse_save_command(parts)
        elif command_name == "resume":
            return self._parse_resume_command(parts)
        elif command_name == "goto":
            return self._parse_goto_command(parts)
        elif command_name == "alias":
            return self._parse_alias_command(parts)
        else:
            raise ValueError(f"Unknown command: {command_name}")

    def _parse_start_command(self, parts: list) -> ParsedCommand:
        """
        Parse :start command.

        Expected format: :start <room_name> <x_cm> <y_cm> <orientation>

        Args:
            parts: Command parts (including 'start')

        Returns:
            ParsedCommand with room_name, x_cm, y_cm, orientation

        Raises:
            ValueError: If syntax is invalid
        """
        if len(parts) != 5:
            raise ValueError(
                "Invalid :start syntax. Expected: :start <room_name> <x_cm> <y_cm> <orientation>"
            )

        room_name = parts[1]

        # Parse coordinates as floats (in cm)
        try:
            x_cm = float(parts[2])
            y_cm = float(parts[3])
        except ValueError:
            raise ValueError("Coordinates x_cm and y_cm must be numbers")

        # Parse orientation
        orientation = parts[4].upper()
        valid_orientations = ["NORTH", "SOUTH", "EAST", "WEST"]

        if orientation not in valid_orientations:
            raise ValueError(
                f"Invalid orientation '{orientation}'. Must be one of: {', '.join(valid_orientations)}"
            )

        return ParsedCommand(
            command="start",
            params={
                "room_name": room_name,
                "x_cm": x_cm,
                "y_cm": y_cm,
                "orientation": orientation
            }
        )

    def _parse_save_command(self, parts: list) -> ParsedCommand:
        """
        Parse :save command.

        Expected format: :save

        Args:
            parts: Command parts (including 'save')

        Returns:
            ParsedCommand with no additional params

        Raises:
            ValueError: If syntax is invalid
        """
        if len(parts) != 1:
            raise ValueError("Invalid :save syntax. Expected: :save (no arguments)")

        return ParsedCommand(
            command="save",
            params={}
        )

    def _parse_resume_command(self, parts: list) -> ParsedCommand:
        """
        Parse :resume command.

        Expected format: :resume

        Args:
            parts: Command parts (including 'resume')

        Returns:
            ParsedCommand with no additional params

        Raises:
            ValueError: If syntax is invalid
        """
        if len(parts) != 1:
            raise ValueError("Invalid :resume syntax. Expected: :resume (no arguments)")

        return ParsedCommand(
            command="resume",
            params={}
        )

    def _parse_goto_command(self, parts: list) -> ParsedCommand:
        """
        Parse :goto command.

        Expected format: :goto <room_name> <start_alias> <end_alias>

        Args:
            parts: Command parts (including 'goto')

        Returns:
            ParsedCommand with room_name, start_alias, end_alias

        Raises:
            ValueError: If syntax is invalid
        """
        if len(parts) != 4:
            raise ValueError(
                "Invalid :goto syntax. Expected: :goto <room_name> <start_alias> <end_alias>"
            )

        return ParsedCommand(
            command="goto",
            params={
                "room_name": parts[1],
                "start_alias": parts[2],
                "end_alias": parts[3]
            }
        )

    def _parse_alias_command(self, parts: list) -> ParsedCommand:
        """
        Parse :alias command.

        Expected format: :alias <room_name> <polygon_idx> <edge_idx> <alias>

        Args:
            parts: Command parts (including 'alias')

        Returns:
            ParsedCommand with room_name, polygon_idx, edge_idx, alias

        Raises:
            ValueError: If syntax is invalid
        """
        if len(parts) != 5:
            raise ValueError(
                "Invalid :alias syntax. Expected: :alias <room_name> <polygon_idx> <edge_idx> <alias>"
            )

        # Parse indices
        try:
            polygon_idx = int(parts[2])
            edge_idx = int(parts[3])
        except ValueError:
            raise ValueError("polygon_idx and edge_idx must be integers")

        return ParsedCommand(
            command="alias",
            params={
                "room_name": parts[1],
                "polygon_idx": polygon_idx,
                "edge_idx": edge_idx,
                "alias": parts[4]
            }
        )

    def handle_key_press(self, key: str):
        """
        Handle a key press event in mapping mode.

        Supported keys:
        - UP: Start moving forward (duration tracked until release)
        - LEFT: Turn left 90 degrees (instant, no duration)
        - RIGHT: Turn right 90 degrees (instant, no duration)
        - COLON: Switch to command mode

        Args:
            key: Key identifier (UP, LEFT, RIGHT, COLON)

        Raises:
            RuntimeError: If brain is not connected or mapping is not active
        """
        if self._mode != Mode.MAPPING_MODE and key != "COLON":
            # Allow COLON in any mode to enter command mode
            return

        key = key.upper()

        if key == "UP":
            self._handle_forward_press()
        elif key == "LEFT":
            self._handle_turn_left()
        elif key == "RIGHT":
            self._handle_turn_right()
        elif key == "COLON":
            self.enter_command_mode()

    def handle_key_release(self, key: str):
        """
        Handle a key release event in mapping mode.

        For UP key: calculates duration and records movement.
        For LEFT/RIGHT: no action (turns are instant).

        Args:
            key: Key identifier (UP, LEFT, RIGHT)

        Raises:
            RuntimeError: If brain is not connected or mapping is not active
        """
        if self._mode != Mode.MAPPING_MODE:
            return

        key = key.upper()

        if key == "UP":
            self._handle_forward_release()

    def _handle_forward_press(self):
        """Handle UP key press - start forward movement."""
        if self._brain is None:
            raise RuntimeError("Cannot control robot: Brain not connected")

        # Only record start time if this is the initial press (not a repeat)
        if self._current_key != "UP" or self._key_press_start_time is None:
            self._key_press_start_time = time.time()
            self._current_key = "UP"

            # Call robot to start moving
            # In real implementation, this would send command to physical robot
            self._brain.robot.move_forward()

    def _handle_forward_release(self):
        """Handle UP key release - stop movement and record duration."""
        if self._brain is None:
            raise RuntimeError("Cannot control robot: Brain not connected")

        if self._current_key != "UP" or self._key_press_start_time is None:
            # Key wasn't pressed or already released
            return

        # Calculate duration
        end_time = time.time()
        duration = end_time - self._key_press_start_time

        # Stop robot
        self._brain.robot.stop()

        # Record movement in brain
        self._brain.record_movement(duration)

        # Reset tracking
        self._key_press_start_time = None
        self._current_key = None

    def _handle_turn_left(self):
        """Handle LEFT key press - turn 90 degrees left (instant)."""
        if self._brain is None:
            raise RuntimeError("Cannot control robot: Brain not connected")

        # Turn is instant, no duration tracking needed
        self._brain.robot.turn_left()

    def _handle_turn_right(self):
        """Handle RIGHT key press - turn 90 degrees right (instant)."""
        if self._brain is None:
            raise RuntimeError("Cannot control robot: Brain not connected")

        # Turn is instant, no duration tracking needed
        self._brain.robot.turn_right()

    def execute_command(self, parsed_command: ParsedCommand) -> str:
        """
        Execute a parsed command.

        Args:
            parsed_command: The ParsedCommand object to execute

        Returns:
            str: Success message describing what was done

        Raises:
            RuntimeError: If brain is not connected
            ValueError: If command execution fails
        """
        if self._brain is None:
            raise RuntimeError("Cannot execute command: Brain not connected")

        command = parsed_command.command
        params = parsed_command.params

        if command == "start":
            return self._execute_start_command(params)
        elif command == "save":
            return self._execute_save_command(params)
        elif command == "resume":
            return self._execute_resume_command(params)
        elif command == "goto":
            return self._execute_goto_command(params)
        elif command == "alias":
            return self._execute_alias_command(params)
        else:
            raise ValueError(f"Unknown command: {command}")

    def _execute_start_command(self, params: Dict[str, Any]) -> str:
        """
        Execute :start command - begin mapping a room.

        Args:
            params: Command parameters (room_name, x_cm, y_cm, orientation)

        Returns:
            str: Success message
        """
        room_name = params["room_name"]
        x_cm = params["x_cm"]
        y_cm = params["y_cm"]
        orientation = params["orientation"]

        # Start mapping session in brain
        self._brain.start_mapping(room_name, x_cm, y_cm, orientation)

        # Switch to mapping mode
        self.enter_mapping_mode()

        return f"Started mapping '{room_name}' from ({x_cm}, {y_cm}) facing {orientation}"

    def _execute_save_command(self, params: Dict[str, Any]) -> str:
        """
        Execute :save command - save the current room.

        Args:
            params: Command parameters (empty for save)

        Returns:
            str: Success message
        """
        # Get room name before saving (it gets cleared after save)
        room_name = self._brain._current_room_name

        if room_name is None:
            raise RuntimeError("No active mapping session to save")

        # Save the room (tolerance in cm)
        self._brain.save_room(tolerance_cm=50.0)

        # Get room info for reporting
        room = self._brain.world_map.get_room(room_name)
        if room:
            num_polygons = len(room.polygons)
            num_points = sum(len(polygon) for polygon in room.polygons)
            report_msg = f"Room '{room_name}' saved with {num_polygons} polygon(s), {num_points} boundary points"
        else:
            report_msg = f"Room '{room_name}' saved"

        # Stay in command mode (mapping ended when room was saved)
        self.enter_command_mode()

        return report_msg

    def _execute_resume_command(self, params: Dict[str, Any]) -> str:
        """
        Execute :resume command - return to mapping mode without saving.

        Args:
            params: Command parameters (empty for resume)

        Returns:
            str: Success message
        """
        if not self._brain.is_mapping_active():
            raise RuntimeError("No active mapping session to resume")

        # Switch to mapping mode
        self.enter_mapping_mode()

        return "Resumed mapping mode"

    def _execute_goto_command(self, params: Dict[str, Any]) -> str:
        """
        Execute :goto command - navigate along room perimeter from one edge to another.

        Args:
            params: Command parameters (room_name, start_alias, end_alias)

        Returns:
            str: Success message with navigation details
        """
        room_name = params["room_name"]
        start_alias = params["start_alias"]
        end_alias = params["end_alias"]

        # Generate navigation waypoints
        waypoints = self._brain.navigate_to_edge(room_name, start_alias, end_alias)

        # Execute the navigation (for now, just report the plan)
        num_waypoints = len(waypoints)
        start_pos = waypoints[0]
        end_pos = waypoints[-1]

        return (
            f"Navigation path from '{start_alias}' to '{end_alias}' in '{room_name}': "
            f"{num_waypoints} waypoints from ({start_pos[0]:.1f}, {start_pos[1]:.1f}) "
            f"to ({end_pos[0]:.1f}, {end_pos[1]:.1f})"
        )

    def _execute_alias_command(self, params: Dict[str, Any]) -> str:
        """
        Execute :alias command - assign an alias to a room edge.

        Args:
            params: Command parameters (room_name, polygon_idx, edge_idx, alias)

        Returns:
            str: Success message
        """
        room_name = params["room_name"]
        polygon_idx = params["polygon_idx"]
        edge_idx = params["edge_idx"]
        alias = params["alias"]

        # Get the room
        room = self._brain.world_map.get_room(room_name)
        if room is None:
            raise ValueError(f"Room '{room_name}' not found")

        # Set the edge alias
        room.set_edge_alias(polygon_idx, edge_idx, alias)

        # Get edge points for reporting
        start_point, end_point = room.get_edge_points(polygon_idx, edge_idx)

        return (
            f"Assigned alias '{alias}' to edge {edge_idx} of polygon {polygon_idx} in '{room_name}' "
            f"[({start_point.x_cm:.1f}, {start_point.y_cm:.1f}) -> ({end_point.x_cm:.1f}, {end_point.y_cm:.1f})]"
        )
