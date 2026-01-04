"""
Visualizer Module

Real-time terminal UI for displaying the vacuum mapping process using Textual framework.
"""

from typing import Tuple, List, Optional
import asyncio
import logging
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Header, Footer
from textual.containers import Container, Vertical
from textual import events
from rich.text import Text
from rich.console import Console, RenderableType
from rich.table import Table

from src.room import WorldMap
from src.controller import Mode

# Set up file logging
logging.basicConfig(
    filename='vacuum_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'  # Overwrite log file each run
)
logger = logging.getLogger(__name__)


class MapGrid(Static):
    """
    Custom Textual widget for rendering the dynamic grid map.

    The grid starts at 2x2 and doubles in size when the map exceeds current bounds.
    Displays cells with different symbols:
    - '.' for empty/unmapped cells
    - First letter of room name for mapped rooms (K, L, B, etc.)
    - Directional arrows (^>v<) for robot position
    - '*' for current path being traced (before save)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._world_map: Optional[WorldMap] = None
        self._robot_pos: Optional[Tuple[int, int]] = None
        self._robot_orientation: Optional[str] = None
        self._current_path_cells: List[Tuple[int, int]] = []  # Converted from cm
        self._grid_size = 2  # Start with 2x2 grid
        self._cell_size_cm = 30.0  # Cell size for conversion

    def update_map_data(
        self,
        world_map: WorldMap,
        robot_pos: Tuple[int, int],
        robot_orientation: str,
        current_path_cm: List[Tuple[float, float, str]],
        cell_size_cm: float
    ):
        """
        Update the map data and trigger a re-render.
        Converts cm-based path to cells on-the-fly.

        Args:
            world_map: The WorldMap containing rooms in cm
            robot_pos: Current robot position (x, y) in cells
            robot_orientation: Robot orientation (NORTH/SOUTH/EAST/WEST)
            current_path_cm: List of (x_cm, y_cm, orientation) tuples
            cell_size_cm: Cell size for conversion
        """
        self._world_map = world_map
        self._robot_pos = robot_pos
        self._robot_orientation = robot_orientation
        self._cell_size_cm = cell_size_cm

        # Convert current path from cm to cells
        self._current_path_cells = [
            (int(x_cm // cell_size_cm), int(y_cm // cell_size_cm))
            for x_cm, y_cm, _ in current_path_cm
        ]

        # Update grid size if needed
        self._update_grid_size()

        # Trigger re-render
        self.update(self._render_grid())

    def _update_grid_size(self):
        """
        Dynamically adjust grid size based on current map bounds.
        Grid doubles when map exceeds current size: 2→4→8→16→32...
        """
        if not self._world_map:
            return

        # Calculate bounds from all mapped cells and current path
        bounds = self._calculate_bounds()
        if not bounds:
            return

        min_x, max_x, min_y, max_y = bounds

        # Calculate required grid size (needs to fit from min to max)
        width_needed = max_x - min_x + 1
        height_needed = max_y - min_y + 1
        max_dimension = max(width_needed, height_needed)

        # Find next power of 2 that fits the map
        # Start with minimum of 2
        new_size = 2
        while new_size < max_dimension:
            new_size *= 2

        # Update if changed
        if new_size != self._grid_size:
            self._grid_size = new_size

    def _calculate_bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Calculate the bounding box of all mapped rooms (converted to cells) and current path.

        Returns:
            Tuple of (min_x, max_x, min_y, max_y) or None if no data
        """
        all_positions = []

        # Add all mapped room boundaries (convert cm to cells)
        if self._world_map:
            for room in self._world_map.get_all_rooms():
                for polygon in room.polygons:
                    for point in polygon:
                        cell_x = int(point.x_cm // self._cell_size_cm)
                        cell_y = int(point.y_cm // self._cell_size_cm)
                        all_positions.append((cell_x, cell_y))

        # Add current path positions (already in cells)
        all_positions.extend(self._current_path_cells)

        # Add robot position
        if self._robot_pos:
            all_positions.append(self._robot_pos)

        # If no positions, include origin
        if not all_positions:
            all_positions.append((0, 0))

        x_coords = [pos[0] for pos in all_positions]
        y_coords = [pos[1] for pos in all_positions]

        return (min(x_coords), max(x_coords), min(y_coords), max(y_coords))

    def _line_intersects_rect(self, x1: float, y1: float, x2: float, y2: float,
                              rect_x_min: float, rect_y_min: float,
                              rect_x_max: float, rect_y_max: float) -> bool:
        """
        Check if a line segment intersects a rectangle.

        Uses the Liang-Barsky line clipping algorithm.

        Args:
            x1, y1: First endpoint of line segment (cm)
            x2, y2: Second endpoint of line segment (cm)
            rect_x_min, rect_y_min: Rectangle min corner (cm)
            rect_x_max, rect_y_max: Rectangle max corner (cm)

        Returns:
            True if line intersects rectangle
        """
        # Check if either endpoint is inside the rectangle
        if (rect_x_min <= x1 <= rect_x_max and rect_y_min <= y1 <= rect_y_max):
            return True
        if (rect_x_min <= x2 <= rect_x_max and rect_y_min <= y2 <= rect_y_max):
            return True

        # Check intersection with rectangle edges
        # Top edge
        if self._segments_intersect(x1, y1, x2, y2, rect_x_min, rect_y_max, rect_x_max, rect_y_max):
            return True
        # Bottom edge
        if self._segments_intersect(x1, y1, x2, y2, rect_x_min, rect_y_min, rect_x_max, rect_y_min):
            return True
        # Left edge
        if self._segments_intersect(x1, y1, x2, y2, rect_x_min, rect_y_min, rect_x_min, rect_y_max):
            return True
        # Right edge
        if self._segments_intersect(x1, y1, x2, y2, rect_x_max, rect_y_min, rect_x_max, rect_y_max):
            return True

        return False

    def _segments_intersect(self, x1: float, y1: float, x2: float, y2: float,
                           x3: float, y3: float, x4: float, y4: float) -> bool:
        """
        Check if two line segments intersect.

        Args:
            x1, y1, x2, y2: Endpoints of first segment
            x3, y3, x4, y4: Endpoints of second segment

        Returns:
            True if segments intersect
        """
        def ccw(ax, ay, bx, by, cx, cy):
            return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)

        return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and
                ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))

    def _cell_intersects_polygon(self, cell_x: int, cell_y: int, polygon) -> bool:
        """
        Check if a cell's bounding box intersects any edge of a polygon.

        Args:
            cell_x: Cell X coordinate (in cells)
            cell_y: Cell Y coordinate (in cells)
            polygon: List of Point objects (in cm)

        Returns:
            True if cell intersects any polygon edge
        """
        # Calculate cell bounds in cm
        cell_x_min = cell_x * self._cell_size_cm
        cell_x_max = (cell_x + 1) * self._cell_size_cm
        cell_y_min = cell_y * self._cell_size_cm
        cell_y_max = (cell_y + 1) * self._cell_size_cm

        # Check each edge of the polygon
        n = len(polygon)
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]  # Wrap around to close polygon

            if self._line_intersects_rect(p1.x_cm, p1.y_cm, p2.x_cm, p2.y_cm,
                                         cell_x_min, cell_y_min, cell_x_max, cell_y_max):
                return True

        return False

    def _get_cell_symbol(self, x: int, y: int) -> str:
        """
        Get the symbol to display for a cell at position (x, y).
        Converts cell to cm and uses point-in-polygon test on rooms.
        Also checks edge intersection for boundary cells.

        Priority:
        1. Robot position → arrow (^>v<)
        2. Current path (not saved) → *
        3. Mapped room (interior) → first letter of room name
        4. Mapped room (boundary) → first letter of room name
        5. Empty/unmapped → .

        Args:
            x: X-coordinate (in cells)
            y: Y-coordinate (in cells)

        Returns:
            Single character symbol for the cell
        """
        # Check if robot is at this position
        if self._robot_pos and self._robot_pos == (x, y):
            return self._get_orientation_arrow()

        # Check if in current path (not yet saved)
        if (x, y) in self._current_path_cells:
            return '*'

        # Check if it's inside a mapped room (point-in-polygon test)
        # Convert cell center to cm coordinates
        x_cm = (x + 0.5) * self._cell_size_cm
        y_cm = (y + 0.5) * self._cell_size_cm

        if self._world_map:
            room_name = self._world_map.get_room_at_position(x_cm, y_cm)
            if room_name:
                return room_name[0].upper()

            # Cell center not inside - check if cell intersects polygon boundary
            for room in self._world_map.get_all_rooms():
                for polygon in room.polygons:
                    if self._cell_intersects_polygon(x, y, polygon):
                        return room.name[0].upper()

        # Empty/unmapped cell
        return '.'

    def _get_orientation_arrow(self) -> str:
        """
        Get the arrow symbol for the robot's current orientation.

        Returns:
            Arrow character (^, >, v, or <)
        """
        arrows = {
            "NORTH": "^",
            "EAST": ">",
            "SOUTH": "v",
            "WEST": "<"
        }
        return arrows.get(self._robot_orientation, "?")

    def _render_grid(self) -> RenderableType:
        """
        Render the grid as a Rich Table.

        Returns:
            Rich Table object ready for rendering
        """
        # Calculate bounds
        bounds = self._calculate_bounds()
        if not bounds:
            return Text("No map data available")

        min_x, max_x, min_y, max_y = bounds

        # Center the map in the grid_size
        # Calculate padding needed
        width = max_x - min_x + 1
        height = max_y - min_y + 1

        # Determine rendering bounds (expand to grid_size if smaller)
        render_width = max(width, self._grid_size)
        render_height = max(height, self._grid_size)

        # Center the actual map within the render area
        x_padding = (render_width - width) // 2
        y_padding = (render_height - height) // 2

        render_min_x = min_x - x_padding
        render_max_x = render_min_x + render_width - 1
        render_min_y = min_y - y_padding
        render_max_y = render_min_y + render_height - 1

        # Create table for grid
        table = Table(show_header=False, show_edge=False, padding=0, box=None)

        # Add columns (include one for y-axis labels)
        table.add_column("Y", justify="right", style="dim")
        for x in range(render_min_x, render_max_x + 1):
            table.add_column(str(x), justify="center", width=2)

        # Add rows (from top to bottom, so highest y first)
        for y in range(render_max_y, render_min_y - 1, -1):
            row_cells = [f"{y:3d}"]  # Y-axis label
            for x in range(render_min_x, render_max_x + 1):
                symbol = self._get_cell_symbol(x, y)

                # Add styling based on symbol type
                if symbol == '^' or symbol == '>' or symbol == 'v' or symbol == '<':
                    # Robot - bright and bold
                    row_cells.append(f"[bold yellow]{symbol}[/bold yellow]")
                elif symbol == '*':
                    # Current path - cyan
                    row_cells.append(f"[cyan]{symbol}[/cyan]")
                elif symbol != '.':
                    # Room cells - green
                    row_cells.append(f"[green]{symbol}[/green]")
                else:
                    # Empty cells - dim
                    row_cells.append(f"[dim]{symbol}[/dim]")

            table.add_row(*row_cells)

        # Add x-axis labels at bottom
        x_labels = ["   "]  # Empty for y-axis column
        for x in range(render_min_x, render_max_x + 1):
            x_labels.append(f"{x:2d}")
        table.add_row(*[f"[dim]{label}[/dim]" for label in x_labels])

        # Add title showing grid size
        title = Text()
        title.append(f"Map Grid (Size: {self._grid_size}×{self._grid_size})", style="bold")

        # Combine title and table
        from rich.console import Group
        return Group(title, table)

    def render(self) -> RenderableType:
        """
        Textual calls this to render the widget.

        Returns:
            Renderable content
        """
        if self._world_map is None:
            return Text("Initializing map...", style="italic")

        return self._render_grid()


class StatusBar(Static):
    """
    Status bar widget showing current mode, robot state, and command prompt.

    Displays 3 lines:
    - Line 1: Current mode (COMMAND_MODE / MAPPING_MODE)
    - Line 2: Robot position (x, y) and orientation
    - Line 3: Current room being mapped OR command prompt/message
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode = Mode.COMMAND_MODE
        self._robot_pos = (0, 0)
        self._robot_orientation = "NORTH"
        self._current_room: Optional[str] = None
        self._message: str = "Type :help for commands"
        self._robot_pos_cm: Optional[Tuple[float, float]] = None

    def update_status(
        self,
        mode: Mode,
        robot_pos: Tuple[int, int],
        robot_orientation: str,
        current_room: Optional[str] = None,
        message: str = "",
        robot_pos_cm: Optional[Tuple[float, float]] = None
    ):
        """
        Update the status bar with new information.

        Args:
            mode: Current mode (COMMAND_MODE or MAPPING_MODE)
            robot_pos: Robot position (x, y) in grid cells
            robot_orientation: Robot orientation (NORTH/SOUTH/EAST/WEST)
            current_room: Name of room being mapped (None if not mapping)
            message: Custom message to display on line 3
            robot_pos_cm: Optional precise position in cm for debugging
        """
        self._mode = mode
        self._robot_pos = robot_pos
        self._robot_orientation = robot_orientation
        self._current_room = current_room
        self._robot_pos_cm = robot_pos_cm
        if message:
            self._message = message

        self.update(self._render_status())

    def _render_status(self) -> RenderableType:
        """
        Render the status bar content.

        Returns:
            Rich Text object with 3 lines
        """
        text = Text()

        # Line 1: Mode
        if self._mode == Mode.COMMAND_MODE:
            text.append("Mode: ", style="bold")
            text.append("COMMAND", style="bold cyan")
        else:
            text.append("Mode: ", style="bold")
            text.append("MAPPING", style="bold yellow")

        text.append("\n")

        # Line 2: Robot position and orientation
        text.append(f"Position: ", style="bold")
        text.append(f"({self._robot_pos[0]}, {self._robot_pos[1]})", style="green")

        # Show cm position if available (for debugging)
        if self._robot_pos_cm:
            text.append(f" [{self._robot_pos_cm[0]:.1f}, {self._robot_pos_cm[1]:.1f}cm]", style="dim green")

        text.append(f" | Orientation: ", style="bold")
        text.append(f"{self._robot_orientation}", style="green")

        text.append("\n")

        # Line 3: Room or message
        if self._current_room:
            text.append(f"Mapping room: ", style="bold")
            text.append(f"{self._current_room}", style="magenta")
        else:
            text.append(self._message, style="dim italic")

        return text

    def render(self) -> RenderableType:
        """
        Textual calls this to render the widget.

        Returns:
            Renderable content
        """
        return self._render_status()


class SmartVacuumApp(App):
    """
    Main Textual application for the Smart Vacuum Mapper.

    Displays a real-time grid map and status bar, handles user input
    through keyboard events and command input.
    """

    CSS = """
    MapGrid {
        height: 1fr;
        border: solid green;
    }

    StatusBar {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 0 1;
    }

    Input {
        dock: bottom;
        display: none;
    }

    Input.visible {
        display: block;
    }
    """

    def __init__(self, brain, controller, event_queue: asyncio.Queue):
        """
        Initialize the Textual app.

        Args:
            brain: Brain instance for accessing state
            controller: Controller instance for handling commands
            event_queue: Async queue for pynput events
        """
        super().__init__()
        self.brain = brain
        self.controller = controller
        self.event_queue = event_queue

        # Widgets (will be set in compose)
        self.map_grid: Optional[MapGrid] = None
        self.status_bar: Optional[StatusBar] = None
        self.command_input: Optional[Input] = None

    def compose(self) -> ComposeResult:
        """
        Compose the application layout.

        Returns:
            Iterator of widgets to display
        """
        self.map_grid = MapGrid(id="map_grid")
        self.status_bar = StatusBar(id="status_bar")
        self.command_input = Input(placeholder="Enter command (e.g., :start kitchen 0 0 NORTH)", id="command_input")

        yield self.map_grid
        yield self.status_bar
        yield self.command_input

    def on_mount(self) -> None:
        """Called when app is mounted - initialize display."""
        self.update_display()

        # Set up periodic event queue processing
        self.set_interval(0.05, self.process_pynput_events)

    async def process_pynput_events(self) -> None:
        """
        Process events from the pynput queue.

        This runs periodically to handle keyboard events from pynput.
        """
        try:
            while not self.event_queue.empty():
                event_type, key = self.event_queue.get_nowait()

                # Convert pynput key to string
                from pynput import keyboard
                key_str = None

                if key == keyboard.Key.up:
                    key_str = "UP"
                elif key == keyboard.Key.down:
                    key_str = "DOWN"
                elif key == keyboard.Key.left:
                    key_str = "LEFT"
                elif key == keyboard.Key.right:
                    key_str = "RIGHT"
                elif hasattr(key, 'char') and key.char == ':':
                    key_str = "COLON"

                if key_str:
                    logger.debug(f"Detected {event_type}: {key_str}")
                    if event_type == 'key_press':
                        await self.handle_pynput_press(key_str)
                    elif event_type == 'key_release':
                        await self.handle_pynput_release(key_str)
                else:
                    logger.debug(f"Ignored key: {key}")

        except asyncio.QueueEmpty:
            pass
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
            self.notify(f"Error processing event: {e}", severity="error")

    async def handle_pynput_press(self, key: str) -> None:
        """
        Handle key press from pynput.

        Args:
            key: Key identifier (UP, LEFT, RIGHT, COLON)
        """
        if key == "COLON" and not self.command_input.has_class("visible"):
            # Show command input
            self.command_input.add_class("visible")
            self.command_input.focus()
            return

        if self.controller.get_mode() == Mode.MAPPING_MODE:
            try:
                logger.info(f"Key press: {key}")
                self.controller.handle_key_press(key)
                self.update_display()
            except Exception as e:
                logger.error(f"Error on key press: {e}", exc_info=True)
                self.notify(f"Error: {e}", severity="error")

    async def handle_pynput_release(self, key: str) -> None:
        """
        Handle key release from pynput.

        Args:
            key: Key identifier (UP, LEFT, RIGHT)
        """
        if self.controller.get_mode() == Mode.MAPPING_MODE:
            try:
                logger.info(f"Key release: {key}")
                pos_before = self.brain.get_position()
                self.controller.handle_key_release(key)
                pos_after = self.brain.get_position()
                logger.info(f"Position: {pos_before} -> {pos_after}")
                logger.info(f"Current path length: {len(self.brain._current_path_cm)}")
                self.update_display()
                logger.info("Display updated")
            except Exception as e:
                logger.error(f"Error on key release: {e}", exc_info=True)
                self.notify(f"Error: {e}", severity="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle command input submission.

        Args:
            event: Input submission event
        """
        command = event.value.strip()

        # Hide input
        self.command_input.remove_class("visible")
        self.command_input.value = ""
        self.map_grid.focus()

        if not command:
            return

        # Handle special commands
        if command == ":help":
            self.show_help()
            return
        elif command == ":rooms":
            self.show_rooms()
            return
        elif command == ":quit":
            self.exit()
            return

        # Handle controller commands
        try:
            parsed = self.controller.parse_command(command)
            result = self.controller.execute_command(parsed)
            self.notify(result, severity="information")
            self.update_display()
        except ValueError as e:
            self.notify(f"Error: {e}", severity="error")
        except RuntimeError as e:
            self.notify(f"Error: {e}", severity="error")
        except Exception as e:
            self.notify(f"Unexpected error: {e}", severity="error")

    def update_display(self) -> None:
        """Update all display widgets with current state."""
        if not self.map_grid or not self.status_bar:
            return

        # Get current state from brain
        robot_pos = self.brain.get_position()  # Grid cells
        robot_pos_cm = self.brain.get_position_cm()  # Precise cm
        robot_orientation = self.brain.get_orientation()
        current_path_cm = self.brain._current_path_cm if hasattr(self.brain, '_current_path_cm') else []
        current_room = self.brain._current_room_name if hasattr(self.brain, '_current_room_name') else None
        mode = self.controller.get_mode()
        cell_size_cm = self.brain.config.cell_size_cm

        # Update map grid
        self.map_grid.update_map_data(
            world_map=self.brain.world_map,
            robot_pos=robot_pos,
            robot_orientation=robot_orientation,
            current_path_cm=current_path_cm,
            cell_size_cm=cell_size_cm
        )

        # Update status bar
        message = ""
        if mode == Mode.COMMAND_MODE:
            message = "Press : to enter command, or type :help for help"
        else:
            message = "UP: move, LEFT/RIGHT: turn, :: command mode"

        self.status_bar.update_status(
            mode=mode,
            robot_pos=robot_pos,
            robot_orientation=robot_orientation,
            current_room=current_room,
            message=message,
            robot_pos_cm=robot_pos_cm
        )

    def show_help(self) -> None:
        """Display help message."""
        help_text = """
Commands:
  :start <room_name> <x> <y> <orientation> - Start mapping
  :save - Save current room
  :resume - Resume mapping
  :rooms - List all rooms
  :quit - Exit application

Mapping controls:
  UP - Move forward (hold)
  LEFT - Turn left 90°
  RIGHT - Turn right 90°
  : - Command mode
        """
        self.notify(help_text.strip(), title="Help", timeout=10)

    def show_rooms(self) -> None:
        """Display all mapped rooms."""
        room_names = self.brain.world_map.get_room_names()

        if not room_names:
            self.notify("No rooms mapped yet.", severity="information")
            return

        rooms_text = f"Mapped rooms ({len(room_names)}):\n"
        for room_name in room_names:
            room = self.brain.world_map.get_room(room_name)
            if room:
                num_polygons = len(room.polygons)
                num_points = sum(len(polygon) for polygon in room.polygons)
                rooms_text += f"  - {room_name}: {num_polygons} polygon(s), {num_points} boundary points\n"

        self.notify(rooms_text.strip(), title="Rooms", timeout=8)
