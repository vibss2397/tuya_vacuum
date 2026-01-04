# Smart Vacuum Mapper

Maps rooms using a vacuum robot controlled via arrow keys. Traces perimeters, auto-fills interiors, saves as JSON.

## Quick Start

```bash
pip install -r requirements.txt
python3 main.py
```

## Usage

**Start mapping first room:**
```
:start kitchen 0 0 NORTH
```

**Map perimeter:** Hold UP to move forward (3 sec = 1 cell @ 30cm), LEFT/RIGHT to turn 90°

**Save room:** Press `:` then type `save`

**Continue mapping:** Start next room from existing cell
```
:start bedroom 30 0 EAST
```

**Commands:**
- `:start <room> <x_cm> <y_cm> <orientation>` - Begin mapping (first room must be at 0,0)
- `:save` - Save traced room
- `:resume` - Return to mapping mode
- `:rooms` - List all rooms
- `:quit` - Exit

**Mapping controls:**
- UP - Move forward (hold for distance)
- LEFT/RIGHT - Turn 90°
- `:` - Command mode

## Architecture

**Brain** - Tracks robot state (position in cm), validates paths, auto-completes shapes with 1-2 straight lines, stores polygons as corner points

**Controller** - Parses commands, handles keyboard input with duration tracking

**WorldMap** - Sparse grid storage, point-in-polygon queries for room lookup

**Robot** - Virtual simulation with stubbed methods for real API integration

**Visualizer** - Textual TUI, dynamic grid (2→4→8→16), real-time updates

**Persistence** - JSON save/load with room polygons and calibration config

## Calibration

Default: 10 cm/s speed, 30 cm cells → 3 seconds per cell

Adjust in [main.py](main.py):
```python
config = CalibrationConfig(
    speed_cm_per_sec=10.0,
    cell_size_cm=30.0
)
```

## Map Format

Polygons stored as corner points in cm coordinates. Example `map.json`:
```json
{
  "version": "1.0",
  "config": {"speed_cm_per_sec": 10.0, "cell_size_cm": 30.0},
  "rooms": [
    {
      "name": "kitchen",
      "polygons": [
        [{"x_cm": 0, "y_cm": 0}, {"x_cm": 0, "y_cm": 90}, ...]
      ]
    }
  ]
}
```

## Testing

```bash
pytest tests/        # All tests
pytest tests/unit/   # Unit only
```

## Project Structure

```
src/
  brain.py         - Mapping logic, path tracking, auto-completion
  controller.py    - Command parsing, keyboard input
  robot.py         - Virtual robot simulation
  room.py          - WorldMap, Room, polygon storage
  visualizer.py    - Textual TUI
  persistence.py   - JSON serialization
  polygon_fill.py  - Scanline algorithm
  constants.py     - CalibrationConfig
main.py            - Entry point, asyncio loop
```
