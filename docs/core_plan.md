### **Project Overview: The "Smart" Vacuum Mapper**

#### 1. Project Goal
To create a software system that allows us to build an accurate 2D grid map of a house. This is for a "dumb" vacuum that has no native mapping ability and can only be controlled by basic, timed commands (e.g., "move forward for *t* seconds").

#### 2. The Core Concept: Translating Time into Cells
The entire system is built on translating *how long* you drive the robot into *how many* grid cells it moved.

1.  **Calibration (Manual, One-Time):** We must first find two constants:
    * **Speed:** The robot's speed in centimeters per second (cm/s).
    * **Turn Rate:** The robot's turn speed in degrees per second (deg/s).
2.  **Define a "Cell":** We will decide on a fixed size for our map's grid squares (e.g., 30cm x 30cm, based on the robot's diameter).
3.  **The "Math":** The script will use these constants to translate control time into grid movement.
    * `Distance = Duration (sec) * Speed (cm/s)`
    * `Cells Moved = Distance / Cell Size`

---

#### 3. The Three System Components

The project will have three main parts that work together:

**Component 1: The Controller (The "Hands")**
This is the real-time remote control interface.
* **Action:** A key is **pressed and held**. Three keys will be used:
    1. up key: Move Forward
    2. left key: Turn Left (90 degrees)
    3. right key: Turn Right (90 degrees)
* **Script Response:**
    1.  Sends the "START MOVE" command to the vacuum.
    2.  Records the `start_time`.
* **Action:** The key is **released**.
* **Script Response:**
    1.  Sends the "STOP" command to the vacuum.
    2.  Records the `end_time`.
    3.  Calculates `duration = end_time - start_time`.
    4.  Sends this `duration` to the "Brain" for processing.
* **Action:** Colon key is pressed. This is an escape key that allows user to type a command. The commands used now will be:
    1. `save {room_name}`: Sends a signal to the brain to save all the commands recorded so far to the named room.
    2. `resume`: Escape the escape key mode and return to normal controller operation.
    3. `goto {x} {y}`: Sends a signal to the brain to navigate to the specified coordinates.

**Component 2: The Brain (The "Mapper")**
This is the core script that holds the map and the robot's state. It has 2 main functions:
1. **Receive Durations:** It listens for `duration` and `orientation` messages from the "Controller."
2. **Save rooms:** It listens for `save {room_name}` commands to save the current map state to a file. For now obstacles will also be saved as separate rooms.
3. **World Building**: It is responsible for converting the directions and durations into a grid of cells and mapping out rooms to the cells.
4. **Global Positioning**: The position from where the script starts mapping is considered `(0, 0)` and is maintained globally. Each cell is relative to this starting position.
5. **Storage**: It will store the entire map along with all the constants (speed, turn rate, cell size) in a file for later retrieval.

**Component 3: The Visualizer (The "Eyes")**
A simple UI that reads the `world_map` from the "Brain" and displays it on-screen. This gives us real-time visual feedback as the map is being built.

---

#### 4. Key Features of the "Brain" Mapping System

To make mapping fast and accurate, the "Brain" will support a few special modes:

* **Rectangle Fill:** A fast-mapping tool. Instead of driving over every inch of a room, we can define the corners of a rectangle. The script will then automatically divide the rectangle into grid cells and mark them as "Open" in the map.
* **"Stitching" Method:** We will map complex rooms (like an L-shape) by defining and "stitching" together multiple small rectangles.
All the rectangles in a room will be combined to form the complete room map.
* **"Go To" Function:** An autonomous navigation mode. We can tell the "Brain" a target `(x, y)` coordinate, and it will automatically calculate a safe path (using the "Open" cells it knows) and send the correct sequence of commands to drive the robot there. This is essential for moving from the end of one rectangle to the start of the next.


**Important**:
Currently "Go To" functionality is optional and not to be implemented. Build the system so that it can be extended later to include this feature.

Start with building the system that works as a simulation
but can later on be extended with real robot commands.