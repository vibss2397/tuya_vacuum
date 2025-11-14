# Smart Vacuum Mapper - Knowledge Base

## Project Goal
Build a software system to create accurate 2D grid maps of a house using a "dumb" vacuum that only accepts timed movement commands. The system is initially a simulation with hooks for real robot API integration later.

## Core Concept
Translate time-based commands into grid cell movements using calibration constants:
- **Speed**: cm/s (forward movement)
- **Turn Rate**: deg/s (rotation)
- **Cell Size**: Fixed dimension (e.g., 30cm x 30cm)
- **Formula**: `Distance = Duration × Speed` → `Cells Moved = Distance / Cell Size`

## System Architecture

### Component 1: Controller (Input Interface)
**Purpose**: Capture user input and send timed commands to the vacuum

**Modes**:
1. **Command Mode** (default on startup): User can type commands
2. **Mapping Mode**: Active controller for driving vacuum

**Key Bindings (Mapping Mode)**:
- **Up Arrow** (hold): Move forward - duration tracked from press to release
- **Left Arrow** (press): Turn left 90° (always exactly 90°, hold duration ignored)
- **Right Arrow** (press): Turn right 90° (always exactly 90°, hold duration ignored)
- **Colon (:)**: Enter command mode

**Commands (Command Mode)**:
- `:start room_name x y orientation` - Begin mapping a room from position (x,y) facing orientation (NORTH/SOUTH/EAST/WEST)
  - First room must start at (0,0)
  - Subsequent rooms start from valid previously mapped cells
  - Error if room doesn't exist and (x,y) ≠ (0,0)
- `:save` - Save currently mapped room (auto-fills polygon interior)
- `:resume` - Return to mapping mode without saving

**Controller Actions**:
- On key press: Send START command to vacuum, record start_time
- On key release: Send STOP command, calculate duration, send (duration, direction) to Brain
- On command: Parse and send to Brain

### Component 2: Brain (Core Mapping Logic)
**Purpose**: Maintain world state, convert durations to coordinates, manage map

**Responsibilities**:
1. **Receive movement data**: (duration, direction) from Controller
2. **Track robot state**: Current position (x,y), orientation (NORTH/SOUTH/EAST/WEST)
3. **Build path**: Accumulate all movements for current room mapping session
4. **Polygon fill**: When `:save` received, close the shape (with tolerance) and fill interior cells
5. **Global positioning**: All cells relative to initial (0,0) starting point
6. **Persistence**: Save/load entire map + constants to/from JSON

**Mapping Algorithm**:
- User drives vacuum around perimeter of a room
- System tracks actual path taken (cell by cell)
- On `:save`, validate shape is closed (or nearly closed - auto-connect if close)
- Apply polygon fill algorithm to mark all interior cells as part of the room
- Cell edges form the perimeter boundaries

**Data Structures**:
- World map: Grid of cells with room assignments
- Robot state: (x, y, orientation)
- Constants: speed, turn_rate, cell_size
- Room registry: List of saved rooms with their cell coordinates

**Constraints**:
- Only closed shapes can be saved
- Auto-close shape if robot position is "close enough" to start position
- No overlapping rooms (assumed for now)
- Turns are always exactly 90°
- No "goto" functionality initially (architecture should support future extension)

### Component 3: Visualizer (Display)
**Purpose**: Real-time visual feedback of map as it's built

**Display Requirements**:
- Grid with coordinates
- Current robot position and orientation
- Different rooms (labeled/colored)
- Grid cell boundaries
- Update in real-time as mapping occurs

**Implementation**: Terminal-based or simple HTML (built last)

## Technical Decisions

### Technology Stack
- **Language**: Python
- **Persistence**: JSON format
- **Robot Interface**: Virtual robot object with stubbed methods (comments indicate where real API calls go)

### Coordinate System
- Origin: (0,0) at first room's starting position
- Orientation: Passed at start (NORTH/SOUTH/EAST/WEST)
- Negative coordinates: Supported
- Grid: Cartesian coordinate system

### Workflow
1. Script starts in **command mode**
2. User: `:start room_name x y orientation` → enters **mapping mode**
3. User drives vacuum (arrow keys)
4. User: `:` → enters **command mode**
5. User: `:save` → saves room, stays in command mode
6. User: `:start next_room x y orientation` → repeat

### Future Extensions (Not Implemented Now)
- "Goto" autonomous navigation
- Real robot API integration (replace virtual robot methods)
- Obstacle marking/differentiation
- Partial turns (non-90° angles)
- Non-closed shape handling
- Room overlap detection

## Development Approach
- **Test-driven**: 1-2 unit tests per functionality
- **Incremental**: Each task adds meaningful functionality
- **Simulation-first**: Build with virtual robot, design for easy API integration
- **Duration**: ~2 hours of dev work
