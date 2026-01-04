# Smart Vacuum Mapper: Checkpoint Roadmap

**Goal**: Transform POC → Google Home integration for "Hey Google, clean kitchen"

**Constraints**:
- Manual mapping (human drives vacuum once to create map)
- Vacuum API: 3 commands only (turn left, turn right, move forward)
- No sensors available for autonomous feedback

---

## CHECKPOINT 1: Robot API Integration

**Goal**: Replace virtual robot with real vacuum API calls

### What to Build
- `RobotAPI` class that wraps your vacuum's 3 commands
- Connection management (WiFi/Bluetooth/serial to vacuum)
- Command confirmation (did command succeed?)
- Basic error handling (retry logic, timeouts)

### Deliverable
Can control vacuum from Python code:
```python
robot = RealVacuumRobot(api_url="http://192.168.1.50")
robot.turn_left()   # Actually turns vacuum left
robot.turn_right()  # Actually turns vacuum right
robot.move_forward(duration=3.0)  # Actually moves vacuum
```

### Test Criteria
- [ ] Run existing mapping session but vacuum actually moves
- [ ] Verify all 3 commands work reliably
- [ ] Connection survives for 10+ minute session

### Files to Create/Modify
- New: `src/robot_api.py` - Real vacuum API wrapper
- Modify: `main.py` - Switch from VirtualRobot to RealVacuumRobot
- Modify: `src/robot.py` - Make it an interface/base class

**Effort**: 1 week
**Priority**: CRITICAL
**Dependencies**: None

---

## CHECKPOINT 2: Autonomous Waypoint Following

**Goal**: Robot can navigate to arbitrary (x,y) coordinate without human control

### What to Build
- Path planning algorithm (A* or simple grid-based)
- Convert path to turn/move commands
- Execute command sequence autonomously
- Position tracking (assume perfect movement for now)

### Deliverable
Robot can go from point A to point B:
```python
brain.goto_point(current=(0,0), target=(90,60))
# Robot automatically: moves forward, turns, moves forward, etc.
# Until it reaches target
```

### Test Criteria
- [ ] Place vacuum at (0,0), command it to (90,60), verify it arrives
- [ ] Test navigation across room (multiple turns required)
- [ ] Verify path is reasonably optimal (not excessive turns)

### Implementation Details
- Enhance `brain.py::navigate_to_edge()` to work with arbitrary coords
- Add A* pathfinding for obstacle-free shortest path
- Create `execute_waypoint_sequence()` method
- Convert waypoint list to robot commands (turn angles + move distances)

### Files to Create/Modify
- Modify: `src/brain.py` - Add `goto_point()`, `execute_waypoint_sequence()`
- New: `src/pathfinding.py` - A* algorithm implementation
- Modify: `src/controller.py` - Add autonomous execution mode

**Effort**: 2 weeks
**Priority**: CRITICAL
**Dependencies**: Checkpoint 1

---

## CHECKPOINT 3: Room Coverage Planning

**Goal**: Generate full coverage path for entire room

### What to Build
- Integrate `polygon_fill.py` with `Room` class
- Implement lawnmower pattern generator
- Convert cell coverage to waypoint sequence
- Optimize turn count (minimize back-and-forth)

### Deliverable
Can generate cleaning path for any room:
```python
plan = brain.generate_cleaning_plan("kitchen")
# Returns: [(0,0), (30,0), (60,0), (60,30), (30,30), (0,30), ...]
# (all cell centers in lawnmower pattern)
```

### Test Criteria
- [ ] Generate plan for kitchen, visualize in TUI
- [ ] Verify 100% coverage of all cells in room
- [ ] No waypoint visits same cell twice (efficiency)
- [ ] Path minimizes turns (prefer straight lines)

### Implementation Details
- Add `Room.get_all_cells()` method using `polygon_fill()`
- Create lawnmower pattern: horizontal sweeps, alternating directions
- Sort cells by (y, x) for rows or (x, y) for columns
- Convert cell coordinates to cm coordinates (waypoints)

### Files to Create/Modify
- Modify: `src/room.py` - Add `get_all_cells()` method
- New: `src/coverage_planner.py` - Lawnmower pattern algorithm
- Modify: `src/brain.py` - Add `generate_cleaning_plan(room_name)`

**Effort**: 1 week
**Priority**: HIGH
**Dependencies**: None (pure algorithm)

---

## CHECKPOINT 4: Autonomous Room Cleaning

**Goal**: Robot fully cleans one room on command

### What to Build
- Combine coverage planning + waypoint following
- Add progress tracking (which cells cleaned)
- Basic stuck detection (timeout per waypoint)
- Completion callback

### Deliverable
Single command triggers full room clean:
```python
brain.clean_room("kitchen")
# Robot autonomously:
# 1. Generates coverage plan
# 2. Navigates to each waypoint
# 3. Returns to start position
# 4. Reports completion
```

### Test Criteria
- [ ] Command `:clean kitchen` in TUI, vacuum cleans entire kitchen
- [ ] Progress indicator shows cells cleaned vs remaining
- [ ] Robot completes cleaning and stops
- [ ] Stuck detection triggers if waypoint takes >2x expected time

### Implementation Details
- Create `CleaningTask` class to track progress
- Add TUI visualization for cleaning progress (show completed cells)
- Implement timeout detection per waypoint
- Add recovery logic (abort and report if stuck)

### Files to Create/Modify
- Modify: `src/brain.py` - Add `clean_room(room_name)` orchestration
- Modify: `src/controller.py` - Add `:clean` command parsing
- Modify: `src/visualizer.py` - Show cleaning progress
- New: `src/cleaning_task.py` - Task state management

**Effort**: 1 week
**Priority**: HIGH
**Dependencies**: Checkpoint 2 + Checkpoint 3

---

## CHECKPOINT 5: Charging Station Integration

**Goal**: Robot knows where charger is and can return to it

### What to Build
- Add `dock_location` to map.json
- Manual dock location marking during initial mapping
- "Return to dock" navigation
- Dock detection (arrived at charger)

### Deliverable
Robot returns to charger after cleaning:
```python
brain.mark_dock_location(x=0, y=0)  # During setup
brain.return_to_dock()  # After cleaning
# Robot navigates back to (0,0) and parks
```

### Test Criteria
- [ ] Mark dock during mapping session (`:dock` command)
- [ ] Clean kitchen, then robot automatically returns to charger
- [ ] Dock location persists in map.json after save/load
- [ ] `:return` command works from any position

### Implementation Details
- Extend `map.json` schema with `dock_location: {x_cm, y_cm}`
- Add `:dock` command to mark current position as charger
- Add `:return` command to navigate back to dock
- Use `goto_point()` from Checkpoint 2 for navigation

### Files to Create/Modify
- Modify: `src/persistence.py` - Add dock_location to schema
- Modify: `src/room.py` - Add `WorldMap.dock_location` field
- Modify: `src/brain.py` - Add `mark_dock_location()`, `return_to_dock()`
- Modify: `src/controller.py` - Add `:dock` and `:return` commands

**Effort**: 3 days
**Priority**: MEDIUM
**Dependencies**: Checkpoint 2

---

## CHECKPOINT 6: REST API Server

**Goal**: Expose cleaning commands via HTTP API

### What to Build
- Flask/FastAPI web server
- Endpoints: `/clean/<room_name>`, `/status`, `/return_to_dock`
- Authentication (API key)
- Status reporting (idle/cleaning/returning/stuck)

### Deliverable
Web API for cleaning commands:
```bash
curl -X POST http://localhost:5000/clean/kitchen
# Response: {"status": "started", "task_id": "abc123"}

curl http://localhost:5000/status
# Response: {"state": "cleaning", "room": "kitchen", "progress": 45}
```

### Test Criteria
- [ ] POST /clean/kitchen triggers autonomous cleaning
- [ ] GET /status returns current state accurately
- [ ] POST /return_to_dock works from any state
- [ ] API key authentication required for all endpoints
- [ ] Server runs in background while robot cleans

### Implementation Details
- Use FastAPI for async support
- Run server in separate thread from main application
- Store cleaning state globally (current task, progress)
- Add CORS headers for web client access

### Files to Create/Modify
- New: `api_server.py` - FastAPI application
- New: `src/api_routes.py` - Route handlers
- Modify: `main.py` - Launch API server in background thread
- New: `requirements.txt` - Add fastapi, uvicorn

**Effort**: 1 week
**Priority**: MEDIUM
**Dependencies**: Checkpoint 4 + Checkpoint 5

---

## CHECKPOINT 7: Google Home Action

**Goal**: Voice command "Hey Google, clean kitchen" triggers cleaning

### What to Build
- Google Actions project setup
- Dialogflow intent for "clean [room]"
- Webhook that calls your REST API
- OAuth for home security
- Fulfillment responses ("Okay, cleaning kitchen now")

### Deliverable
Voice-controlled cleaning:
```
User: "Hey Google, ask vacuum to clean kitchen"
Google: "Okay, starting kitchen cleaning"
[Robot starts cleaning]
Google: "Kitchen cleaning complete" (after 10 mins)
```

### Test Criteria
- [ ] Speak command to Google Home, vacuum starts cleaning
- [ ] Google confirms start and completion
- [ ] Works from any Google Home device on network
- [ ] Handles unknown rooms gracefully ("I don't know that room")

### Implementation Details
- Create Google Actions project at actions.google.com
- Set up Dialogflow with "clean [room]" intent
- Deploy webhook (could be ngrok tunnel to localhost for testing)
- Implement fulfillment: parse room name, call REST API
- Add conversational responses

### Files to Create/Modify
- New: `google_action/` - Dialogflow config files
- New: `webhook.py` - Fulfillment webhook server
- New: `GOOGLE_HOME_SETUP.md` - Setup instructions

**Effort**: 1 week
**Priority**: LOW (after REST API works)
**Dependencies**: Checkpoint 6

---

## CHECKPOINT 8: Multi-Room & Scheduling

**Goal**: Clean multiple rooms, schedule cleanings

### What to Build
- Multi-room routing (which room order is optimal?)
- Scheduled tasks (clean at 2pm every Tuesday)
- Battery management (return to dock if low battery mid-clean)
- Resume cleaning after charging

### Deliverable
Advanced autonomous features:
```
User: "Hey Google, clean the house"
Google: "Okay, cleaning 4 rooms: kitchen, bedroom, living room, bathroom"
[Robot cleans all rooms, returns to dock]
```

### Test Criteria
- [ ] "Clean the house" cleans all mapped rooms efficiently
- [ ] Schedule "clean kitchen every Monday at 10am" works
- [ ] Robot returns to dock if battery low, resumes after charging
- [ ] Multi-room path is optimized (minimal backtracking)

### Implementation Details
- Add task scheduler (APScheduler or similar)
- Implement TSP solver for room ordering
- Add battery level simulation/API integration
- Store cleaning schedules in database (SQLite)

### Files to Create/Modify
- New: `src/scheduler.py` - Task scheduling
- New: `src/multi_room_planner.py` - Route optimization
- Modify: `src/robot_api.py` - Add battery level API
- New: `schedules.db` - SQLite database for tasks

**Effort**: 2 weeks
**Priority**: LOW
**Dependencies**: Checkpoint 7

---

## Priority & Effort Summary

| Checkpoint | Priority | Effort | Dependencies |
|------------|----------|--------|--------------|
| 1. Robot API | **CRITICAL** | 1 week | None |
| 2. Waypoint Following | **CRITICAL** | 2 weeks | #1 |
| 3. Coverage Planning | **HIGH** | 1 week | None |
| 4. Autonomous Cleaning | **HIGH** | 1 week | #2 + #3 |
| 5. Charging Station | **MEDIUM** | 3 days | #2 |
| 6. REST API Server | **MEDIUM** | 1 week | #4 + #5 |
| 7. Google Home Action | **LOW** | 1 week | #6 |
| 8. Multi-Room/Scheduling | **LOW** | 2 weeks | #7 |

**Total Time to Google Home**: 8-10 weeks (part-time)

---

## Technical Decisions Needed

Before starting, answer these questions:

### 1. Which vacuum do you have?
- Brand/model determines API availability
- Some vacuums have local APIs (Roborock, Valetudo)
- Others need cloud APIs (iRobot, Xiaomi)
- Worst case: reverse engineer protocol

### 2. How will vacuum report position?
Given "no sensors" constraint:
- **Dead reckoning**: Assume perfect movement (error accumulates)
- **Manual checkpoints**: User confirms robot reached waypoint
- **Hybrid**: Dead reckoning with occasional manual corrections

### 3. What happens if robot gets stuck?
Options:
- **Timeout + abort**: If waypoint not reached in 2x expected time, give up
- **Manual rescue**: Send notification to phone, user unsticks robot
- **Retry with wiggle**: Back up, turn slightly, try again

### 4. Where should map.json live?
- **Local**: On same machine running Python (Raspberry Pi?)
- **Cloud**: Firebase/AWS for access from anywhere
- **Both**: Local primary, cloud backup

### 5. How to handle updates during cleaning?
- **Blocking**: CLI blocks until cleaning done (simple)
- **Background**: Async task, poll for status (better UX)
- **Websocket**: Real-time progress updates (advanced)

---

## Recommended First 3 Steps

### Step 1: Research Your Vacuum's API (1-2 days)
- Find official API docs (if any)
- Check reverse engineering forums (Valetudo, Home Assistant integrations)
- Test basic commands (turn, move) manually
- Document exact command format

### Step 2: Implement Robot API Wrapper (3-5 days)
```python
# src/robot_api.py (new file)
class RealVacuumRobot:
    def __init__(self, host: str, port: int):
        # Connection to vacuum
        pass

    def turn_left(self):
        # Send actual command
        response = requests.post(f"{self.host}/turn_left")
        return response.status_code == 200

    def turn_right(self):
        # Send actual command
        pass

    def move_forward(self, duration: float):
        # Send actual command with duration
        pass
```

### Step 3: Test Manual Mapping with Real Vacuum (1-2 days)
- Replace `VirtualRobot` with `RealVacuumRobot` in main.py
- Run existing `:start kitchen 0 0 NORTH` workflow
- Verify vacuum actually moves when you press arrow keys
- Debug any timing/communication issues

**After these 3 steps**: You have a working robot-controlled mapper!

---

## What You DON'T Need

Based on your constraints, you can **skip** these:
- ❌ Sensor fusion (no sensors)
- ❌ SLAM (manual mapping only)
- ❌ Real-time obstacle detection (assume clean room)
- ❌ Odometry correction (accept drift)
- ❌ Computer vision (not available)
- ❌ Battery API (if vacuum has none, just estimate)

This significantly reduces complexity!

---

## Simplest Possible MVP

If you want the **absolute minimum** for "Hey Google, clean kitchen":

1. Hardcode vacuum API calls (1 day)
2. Simple grid-based pathfinding (2 days)
3. Lawnmower pattern generator (1 day)
4. Flask server with `/clean/<room>` endpoint (1 day)
5. Google Action that POSTs to Flask (2 days)

**Total**: 1 week for barebones version (assumes many simplifications and no error handling)

---

## Current Status

- ✅ POC Complete: Manual mapping, visualization, persistence
- ⏳ Checkpoint 1: Not started
- ⏳ Checkpoint 2: Partial (`navigate_to_edge()` exists but doesn't execute)
- ⏳ Checkpoint 3: Partial (`polygon_fill.py` exists but not integrated)
- ⏳ Checkpoint 4-8: Not started

**Next Action**: Begin Checkpoint 1 (Robot API Integration)
