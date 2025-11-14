# Smart Vacuum Mapper - Task List

## Milestone 1: Core Data Structures & Robot Simulation

### Task 1.1: Create Virtual Robot Class
**Description**: Implement a virtual robot with stubbed movement methods
**Files**: `robot.py`
**Implementation**:
- Create `VirtualRobot` class with methods:
  - `move_forward()` - stub with comment for real API
  - `stop()` - stub with comment for real API
  - `get_position()` - returns current (x, y)
  - `get_orientation()` - returns current orientation (NORTH/SOUTH/EAST/WEST)
  - `set_position(x, y)` - for simulation
  - `set_orientation(orientation)` - for simulation
**Tests**:
- Test robot initialization at (0,0) with given orientation
- Test position/orientation getters and setters
**Expected Outcome**: Can create a robot object, query/set its position and orientation. Foundation for simulating robot movement.

### Task 1.2: Create Calibration Constants Module
**Description**: Define and manage calibration constants
**Files**: `constants.py`
**Implementation**:
- Define constants: `SPEED_CM_PER_SEC`, `TURN_RATE_DEG_PER_SEC`, `CELL_SIZE_CM`
- Create `CalibrationConfig` class to hold these values
- Add methods to calculate: distance from duration, cells from distance -- note: only dataclass implemented
**Tests**:
- Test distance calculation: duration × speed
- Test cell calculation: distance / cell_size
**Expected Outcome**: Can create a configuration with calibration values that will be used throughout the system for time-to-distance conversions.

### Task 1.3: Create Grid Cell and World Map Data Structures
**Description**: Define data structures for the world map
**Files**: `cell.py`
**Implementation**:
- Create `Cell` class with properties: coordinates (x,y), room_name (optional)
- Create `WorldMap` class with:
  - Grid storage (dict or 2D structure)
  - Methods: `get_cell(x, y)`, `set_cell(x, y, room_name)`, `cell_exists(x, y)`
  - Method: `get_all_cells_for_room(room_name)`
**Tests**:
- Test adding/retrieving cells from map
- Test querying cells by room name
**Expected Outcome**: Can create a map, add cells with room assignments, query cells by coordinates or room name. Core data structure for storing the house map.

## Milestone 2: Brain - Movement Tracking & State Management

### Task 2.1: Create Robot State Tracker
**Description**: Track robot's current position and orientation during mapping
**Files**: `brain.py` (create Brain class)
**Implementation**:
- Create `Brain` class with:
  - Current robot state: position (x,y), orientation
  - Reference to `VirtualRobot` and `WorldMap`
  - Method: `update_position(duration, direction)` - calculates new position based on movement
  - Method: `turn_left()` - updates orientation (NORTH→WEST→SOUTH→EAST→NORTH)
  - Method: `turn_right()` - updates orientation (NORTH→EAST→SOUTH→WEST→NORTH)
**Tests**:
- Test forward movement updates position correctly (e.g., from (0,0) NORTH moving 1 cell → (0,1))
- Test left/right turns update orientation correctly
**Expected Outcome**: Brain can track robot position/orientation, update position based on timed movements, handle 90° turns. Can simulate robot moving forward and turning.

### Task 2.2: Create Path Recording System
**Description**: Record all movements during a mapping session
**Files**: `brain.py` (extend Brain class)
**Implementation**:
- Add to `Brain`:
  - `current_path` list to store all (x,y) positions visited
  - `start_mapping(room_name, x, y, orientation)` - initializes mapping session
  - `record_movement(duration, direction)` - calls `update_position` and appends to path
  - `clear_path()` - resets current_path
  - Validation: first room must start at (0,0), subsequent rooms at valid cells
**Tests**:
- Test path recording accumulates positions correctly
- Test validation: first room at (0,0) passes, first room at (1,1) raises error
**Expected Outcome**: Can start a mapping session, record a sequence of movements as a path, validate starting positions. Brain remembers the perimeter traced by the robot.

## Milestone 3: Brain - Polygon Fill Algorithm

### Task 3.1: Implement Shape Closure Detection
**Description**: Detect if traced path forms a closed (or nearly closed) shape
**Files**: `brain.py` (extend Brain class)
**Implementation**:
- Add method: `is_shape_closed(tolerance=1)`
  - Check if final position is within `tolerance` cells of start position
  - Return True if closed or nearly closed
**Tests**:
- Test exact closure: path returns to start → True
- Test near closure: path within tolerance → True
**Expected Outcome**: Can validate whether a traced path forms a closed shape, with tolerance for real-world imprecision.

### Task 3.2: Implement Polygon Fill Algorithm
**Description**: Fill interior cells of a closed polygon
**Files**: `polygon_fill.py`
**Implementation**:
- Create function: `fill_polygon(path_points)`
  - Use scanline/ray-casting algorithm to find interior cells
  - Return list of (x,y) coordinates for all interior cells
- Integrate into `Brain.save_room()`
**Tests**:
- Test simple rectangle: 4 corners → correct interior cells filled
- Test L-shape polygon → correct interior cells filled
**Expected Outcome**: Given a perimeter path, can automatically fill all interior cells. Core algorithm for converting traced paths into complete room maps.

### Task 3.3: Implement Save Room Functionality
**Description**: Complete the save workflow - close shape, fill, assign to room
**Files**: `brain.py` (extend Brain class)
**Implementation**:
- Add method: `save_room(room_name)`
  - Validate shape is closed (auto-close if within tolerance)
  - Get filled cells from polygon_fill
  - Update WorldMap: assign all cells to room_name
  - Add room to registry
  - Clear current path
**Tests**:
- Test successful save: closed path → cells assigned to room
- Test auto-close: nearly closed path → auto-connects and saves
**Expected Outcome**: Can complete mapping workflow - trace perimeter, save with room name, auto-fill interior. WorldMap now contains the complete room with all cells assigned.

## Milestone 4: Persistence - Save/Load Map

### Task 4.1: Implement Map Serialization
**Description**: Convert WorldMap to JSON format
**Files**: `persistence.py`
**Implementation**:
- Create function: `serialize_map(world_map, constants)`
  - Convert WorldMap and CalibrationConfig to JSON-serializable dict
  - Include: all cells with room assignments, constants, room registry
  - Return JSON string
**Tests**:
- Test serialization: map with 2 rooms → valid JSON structure
- Test includes all required fields (cells, constants, rooms)
**Expected Outcome**: Can convert a complete map with rooms and constants into JSON format for storage.

### Task 4.2: Implement Map Deserialization
**Description**: Load WorldMap from JSON file
**Files**: `persistence.py`
**Implementation**:
- Create function: `deserialize_map(json_string)`
  - Parse JSON and reconstruct WorldMap and CalibrationConfig
  - Return tuple: (world_map, constants)
- Add to Brain: `load_map(filepath)` method
**Tests**:
- Test deserialization: valid JSON → correct WorldMap object
- Test round-trip: serialize then deserialize → identical map
**Expected Outcome**: Can reconstruct a complete WorldMap from JSON, restoring all rooms and settings.

### Task 4.3: Implement Save/Load File Operations
**Description**: Handle file I/O for map persistence
**Files**: `persistence.py`
**Implementation**:
- Create function: `save_to_file(world_map, constants, filepath)`
- Create function: `load_from_file(filepath)`
- Add error handling for file not found, invalid JSON
**Tests**:
- Test save then load: data persists correctly
- Test load non-existent file: raises appropriate error
**Expected Outcome**: Can save maps to disk and load them later. Users can pause mapping, exit, and resume later from saved state.

## Milestone 5: Controller - Input Handling

### Task 5.1: Implement Command Parser
**Description**: Parse user commands in command mode
**Files**: `controller.py` (create Controller class)
**Implementation**:
- Create `Controller` class with:
  - Reference to `Brain`
  - Mode state: COMMAND_MODE or MAPPING_MODE
  - Method: `parse_command(command_string)`
    - Parse `:start room_name x y orientation`
    - Parse `:save`
    - Parse `:resume`
    - Return structured command object or error
**Tests**:
- Test parsing valid start command → correct parameters extracted
- Test parsing invalid command → error raised
**Expected Outcome**: Can parse user commands from text input. Foundation for command-mode interface.

### Task 5.2: Implement Keyboard Input Handler (Mapping Mode)
**Description**: Capture arrow key presses and track durations
**Files**: `controller.py` (extend Controller class)
**Implementation**:
- Add method: `handle_key_press(key)`
  - If UP: record start_time, call robot.move_forward()
  - If LEFT/RIGHT: call brain.turn_left/right()
  - If COLON: switch to COMMAND_MODE
- Add method: `handle_key_release(key)`
  - If UP: record end_time, calculate duration, call brain.record_movement()
**Tests**:
- Test key press/release: correct duration calculated
- Test turn keys: orientation updates in brain
**Expected Outcome**: Can capture arrow key inputs, measure hold duration, send timed commands to Brain. Real-time robot control working.

### Task 5.3: Implement Mode Switching and Main Loop
**Description**: Handle mode transitions and main event loop
**Files**: `controller.py` (extend Controller class)
**Implementation**:
- Add methods:
  - `enter_command_mode()` - switches mode, displays prompt
  - `enter_mapping_mode()` - switches mode
  - `execute_command(parsed_command)` - calls appropriate Brain methods
- Create `run()` method: main event loop
  - If COMMAND_MODE: accept text input
  - If MAPPING_MODE: listen for key events
**Tests**:
- Test mode switching: command → mapping → command
- Test command execution: `:start` triggers brain.start_mapping()
**Expected Outcome**: Complete controller with mode switching. User can type commands, switch to mapping mode, control robot with arrow keys, switch back to commands.

## Milestone 6: Integration & Main Entry Point

### Task 6.1: Create Main Application Entry Point
**Description**: Wire all components together
**Files**: `main.py`
**Implementation**:
- Initialize CalibrationConfig with default values
- Initialize VirtualRobot
- Initialize WorldMap
- Initialize Brain with robot and map
- Initialize Controller with brain
- Check for existing map file, prompt to load if exists
- Start controller.run()
**Tests**:
- Test full workflow simulation: start → map rectangle → save → verify cells
- Test load existing map and continue mapping
**Expected Outcome**: Complete working application! Can run main.py, issue commands, map rooms, save/load maps. All components integrated and functional.

### Task 6.2: Add Basic Error Handling and Validation
**Description**: Add user-friendly error messages and input validation
**Files**: All modules
**Implementation**:
- Add try-catch blocks in controller for invalid commands
- Add validation in brain for invalid coordinates
- Add user-friendly error messages
**Tests**:
- Test invalid start coordinates → clear error message
- Test invalid command syntax → clear error message
**Expected Outcome**: Application handles errors gracefully with clear feedback. Invalid inputs don't crash the program.

## Milestone 7: Visualizer - Display Map

### Task 7.1: Implement Terminal-Based Visualizer
**Description**: Display map in terminal with ASCII art
**Files**: `visualizer.py`
**Implementation**:
- Create `Visualizer` class:
  - Method: `render(world_map, robot_position, robot_orientation)`
  - Display grid with coordinates
  - Show cells with room names (first letter or color code)
  - Show robot position with arrow (^>v<)
  - Method: `update()` - called after each movement
**Tests**:
- Test rendering empty map → displays grid
- Test rendering map with room → room cells displayed correctly
**Expected Outcome**: Can visually see the map in terminal. Shows grid, rooms, robot position/orientation. Makes mapping progress visible.

### Task 7.2: Integrate Visualizer with Controller
**Description**: Update display in real-time during mapping
**Files**: `controller.py`, `main.py`
**Implementation**:
- Add Visualizer to Controller
- Call visualizer.update() after each movement
- Split screen or use clear/redraw for terminal display
**Tests**:
- Test visualization updates after movement (manual/integration test)
**Expected Outcome**: Live visual feedback! Map updates in real-time as robot moves. User can see the mapping happening as they control the robot.

## Milestone 8: Testing & Documentation

### Task 8.1: Integration Testing
**Description**: End-to-end tests for complete workflows
**Files**: `test_integration.py`
**Implementation**:
- Test complete mapping workflow: start → move → save → verify
- Test multi-room mapping: map room1, then room2 starting from room1 cell
- Test save and load: map room, save, load, verify state
**Tests**:
- All integration scenarios pass
**Expected Outcome**: Full test coverage for end-to-end workflows. Confidence that all components work together correctly for real-world usage scenarios.

### Task 8.2: Add Usage Documentation
**Description**: Create README with usage instructions
**Files**: `README.md`
**Implementation**:
- Document how to run the application
- Explain commands and key bindings
- Provide example mapping workflow
- Explain calibration constants
**Expected Outcome**: Complete documentation! New users can understand how to use the system, what commands are available, and how to map their house.

---

## Task Execution Notes
- Each task should be completed sequentially within its milestone
- Milestones can be worked on in order
- All tests must pass before moving to next task
- Code should include comments indicating where real robot API calls will be added
