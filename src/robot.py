"""
Virtual Robot Module

Simulates a physical vacuum robot with basic movement capabilities.
Methods are stubbed for future integration with real robot API.
"""


class VirtualRobot:
    """
    Simulates a vacuum robot with position and orientation tracking.

    In the real implementation, move_forward() and stop() will send
    actual commands to the physical robot via its API.
    """

    def __init__(self, x=0, y=0, orientation="NORTH"):
        """
        Initialize the virtual robot.

        Args:
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            orientation (str): Starting orientation (NORTH/SOUTH/EAST/WEST)
        """
        self._x = x
        self._y = y
        self._orientation = orientation

    def move_forward(self):
        """
        Start moving the robot forward.

        TODO: Replace with actual robot API call
        Example: robot_api.send_command("MOVE_FORWARD")
        """
        # Stub - in simulation, actual movement is handled by Brain
        pass

    def stop(self):
        """
        Stop all robot movement.

        TODO: Replace with actual robot API call
        Example: robot_api.send_command("STOP")
        """
        # Stub - in simulation, no action needed
        pass

    def get_position(self):
        """
        Get the current position of the robot.

        Returns:
            tuple: (x, y) coordinates
        """
        return (self._x, self._y)

    def get_orientation(self):
        """
        Get the current orientation of the robot.

        Returns:
            str: Orientation (NORTH/SOUTH/EAST/WEST)
        """
        return self._orientation

    def set_position(self, x, y):
        """
        Set the robot's position (for simulation purposes).

        Args:
            x (int): New x-coordinate
            y (int): New y-coordinate
        """
        self._x = x
        self._y = y

    def set_orientation(self, orientation):
        """
        Set the robot's orientation (for simulation purposes).

        Args:
            orientation (str): New orientation (NORTH/SOUTH/EAST/WEST)
        """
        valid_orientations = ["NORTH", "SOUTH", "EAST", "WEST"]
        if orientation not in valid_orientations:
            raise ValueError(f"Invalid orientation. Must be one of {valid_orientations}")
        self._orientation = orientation
