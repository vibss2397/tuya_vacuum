#!/usr/bin/env python3
"""
Smart Vacuum Mapper - Main Entry Point

A command-line application for mapping rooms using a vacuum robot.
Controls the robot with arrow keys and saves room layouts to a map.
"""

import sys
import os
import asyncio
from typing import Optional
from pynput import keyboard
from src.robot import VacuumRobot
from src.room import WorldMap
from src.constants import CalibrationConfig
from src.brain import Brain
from src.controller import Controller, Mode
from src.persistence import save_to_file, load_from_file
from src.visualizer import SmartVacuumApp


# Default map file location
DEFAULT_MAP_FILE = "map.json"


class Application:
    """Main application that manages the mapping workflow"""

    def __init__(self, map_file: str = DEFAULT_MAP_FILE):
        """
        Initialize the application.

        Args:
            map_file: Path to save/load map data
        """
        self.map_file = map_file
        self.running = False

        # Initialize components
        self.config = CalibrationConfig(
            speed_cm_per_sec=10.0,
            turn_rate_deg_per_sec=90.0,
            cell_size_cm=30.0
        )
        self.robot = VacuumRobot(config_file='configs/robot_config.yaml')
        self.world_map = WorldMap()
        self.brain = Brain(self.robot, self.world_map, self.config)
        self.controller = Controller(self.brain)

        # Asyncio infrastructure
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.textual_app: Optional[SmartVacuumApp] = None

        # Keyboard listener
        self.keyboard_listener: Optional[keyboard.Listener] = None

    def load_existing_map(self) -> bool:
        """
        Check for existing map file and load if it exists.

        Returns:
            True if map was loaded, False otherwise
        """
        if not os.path.exists(self.map_file):
            return False

        try:
            loaded_map, loaded_config = load_from_file(self.map_file)
            self.world_map = loaded_map
            self.config = loaded_config
            # Reinitialize brain with loaded data
            self.brain = Brain(self.robot, self.world_map, self.config)
            self.controller = Controller(self.brain)

            print(f"Loaded map with {len(self.world_map.get_room_names())} rooms:")
            for room_name in self.world_map.get_room_names():
                room = self.world_map.get_room(room_name)
                if room:
                    num_polygons = len(room.polygons)
                    num_points = sum(len(polygon) for polygon in room.polygons)
                    print(f"  - {room_name}: {num_polygons} polygon(s), {num_points} points")

            return True
        except Exception as e:
            print(f"Error loading map: {e}")
            return False

    def save_map(self):
        """Save the current map to file"""
        try:
            save_to_file(self.world_map, self.config, self.map_file)
            print(f"\nMap saved to {self.map_file}")
        except Exception as e:
            print(f"\nError saving map: {e}")

    def on_key_press(self, key):
        """
        Handle keyboard press events from pynput.

        Bridges pynput events to asyncio queue.

        Args:
            key: The key that was pressed
        """
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(
                    self.event_queue.put_nowait,
                    ('key_press', key)
                )
            except Exception as e:
                print(f"Error queuing key press: {e}")

    def on_key_release(self, key):
        """
        Handle keyboard release events from pynput.

        Bridges pynput events to asyncio queue.

        Args:
            key: The key that was released
        """
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(
                    self.event_queue.put_nowait,
                    ('key_release', key)
                )
            except Exception as e:
                print(f"Error queuing key release: {e}")

    def start_keyboard_listener(self):
        """Start listening for keyboard events"""
        if self.keyboard_listener is None or not self.keyboard_listener.running:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()

    def stop_keyboard_listener(self):
        """Stop listening for keyboard events"""
        if self.keyboard_listener and self.keyboard_listener.running:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    async def run(self):
        """Main application loop (async)"""
        print("=== Smart Vacuum Mapper ===")
        print("Loading...\n")

        # Try to load existing map
        self.load_existing_map()

        # Get the current event loop
        self.loop = asyncio.get_running_loop()

        # Start keyboard listener (runs in separate thread)
        self.start_keyboard_listener()

        self.running = True

        try:
            # Create and run Textual app
            self.textual_app = SmartVacuumApp(
                brain=self.brain,
                controller=self.controller,
                event_queue=self.event_queue
            )

            # Run the Textual app (this will block until app exits)
            await self.textual_app.run_async()

        finally:
            # Clean up
            self.running = False
            self.stop_keyboard_listener()

            # Offer to save map on exit
            if len(self.world_map.get_all_rooms()) > 0:
                print("\nSaving map...")
                self.save_map()

            print("\nGoodbye!")


def main():
    """Entry point for the application"""
    # Check for custom map file
    map_file = DEFAULT_MAP_FILE
    if len(sys.argv) > 1:
        map_file = sys.argv[1]

    # Create application
    app = Application(map_file)

    # Run the async application
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
