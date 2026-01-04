"""
Virtual Robot Module

Simulates a physical vacuum robot with basic movement capabilities.
Methods are stubbed for future integration with real robot API.
"""
import yaml
from tinytuya import Device
import time


class VacuumRobot:
    """
    Simulates a vacuum robot with position and orientation tracking.

    In the real implementation, move_forward() and stop() will send
    actual commands to the physical robot via its API.
    """

    def __init__(self, config_file: str | None = None,  x=0.0, y=0.0, orientation="NORTH"):
        """
        Initialize the virtual robot.

        Args:
            x (float): Starting x-coordinate in cm
            y (float): Starting y-coordinate in cm
            orientation (str): Starting orientation (NORTH/SOUTH/EAST/WEST)
        """
        self._x = float(x)
        self._y = float(y)
        self._orientation = orientation
        self._robot_diameter_cm = 25.0  # Default diameter for calibration reference
        self._robot_speed = 10.0  # cm/s, default speed for simulation
        if config_file:
            with open(config_file, "r") as file:
                config = yaml.safe_load(file)
            self._robot_config = config.get("robot", {})
            self._device = self.init_device()
        else:
            self._robot_config = {}
            self._device = None
    
    def init_device(self) -> Device:
        device_id = self._robot_config.get("connection", {}).get("DEVICE_ID")
        device_ip = self._robot_config.get("connection", {}).get("IP_ADDRESS")
        local_key = self._robot_config.get("connection", {}).get("LOCAL_KEY")
        vacuum = Device(
            dev_id=device_id,
            address=device_ip,
            local_key=local_key,
            version="3.4"
        )
        return vacuum

    def move_forward(self):
        """
        Start moving the robot forward.
        """
        if not self._device:
            # Virtual mode
            return True

        dp_id = self._robot_config.get("dp_mapping", {}).get("direction_control")
        dp_value = "forward"
        try:
            self._device.set_value(dp_id, dp_value)
        except Exception as e:
            print(f"Error setting device value: {e}")
            return False
        return True

    def stop(self):
        """
        Stop all robot movement.
        """
        if not self._device:
            # Virtual mode
            return True

        dp_id = self._robot_config.get("dp_mapping", {}).get("direction_control")
        dp_value = "stop"
        try:
            self._device.set_value(dp_id, dp_value)
        except Exception as e:
            print(f"Error setting device value: {e}")
            return False
        return True

    def turn_left(self):
        """
        Turn the robot left (90 degrees).
        """
        if not self._device:
            # Virtual mode
            self._orientation = self.calculate_orientation(self._orientation, "left")
            return True

        dp_id = self._robot_config.get("dp_mapping", {}).get("direction_control")
        dp_value = "turn_left"
        sleep_val = self._robot_config.get("calibration", {}).get("90_deg_turn_time_sec")
        if dp_id is None or sleep_val is None:
            print("Error: Missing dp_id or sleep_val in configuration.")
            return False
        try:
            self._device.set_value(dp_id, dp_value)
            time.sleep(sleep_val)
            self.stop()
            self._orientation = self.calculate_orientation(self._orientation, "left")
        except Exception as e:
            print(f"Error setting device value: {e}")
            return False
        return True

    def turn_right(self):
        """
        Turn the robot right (90 degrees).
        """
        if not self._device:
            # Virtual mode
            self._orientation = self.calculate_orientation(self._orientation, "right")
            return True

        dp_id = self._robot_config.get("dp_mapping", {}).get("direction_control")
        dp_value = "turn_right"
        sleep_val = self._robot_config.get("calibration", {}).get("90_deg_turn_time_sec")
        if dp_id is None or sleep_val is None:
            print("Error: Missing dp_id or sleep_val in configuration.")
            return False
        try:
            self._device.set_value(dp_id, dp_value)
            time.sleep(sleep_val)
            self.stop()
            self._orientation = self.calculate_orientation(self._orientation, "right")
        except Exception as e:
            print(f"Error setting device value: {e}")
            return False
        return True


    def go_charge(self):
        """
        Start charging the robot.
        """
        if not self._device:
            # Virtual mode
            return True

        dp_id = self._robot_config.get("dp_mapping", {}).get("mode")
        dp_value = "chargego"
        try:
            self._device.set_value(dp_id, dp_value)
        except Exception as e:
            print(f"Error setting device value: {e}")
            return False
        return True

    def get_position(self):
        """
        Get the current position of the robot in cm.

        Returns:
            tuple: (x, y) coordinates in centimeters
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
            x (float): New x-coordinate in cm
            y (float): New y-coordinate in cm
        """
        self._x = float(x)
        self._y = float(y)

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

    def calculate_orientation(self, current_orientation, turn_direction):
        """
        Calculate the new orientation after a turn.
        """
        orientations = ["NORTH", "EAST", "SOUTH", "WEST"]
        idx = orientations.index(current_orientation)
        if turn_direction == "left":
            new_idx = (idx - 1) % 4
        elif turn_direction == "right":
            new_idx = (idx + 1) % 4
        else:
            raise ValueError("turn_direction must be 'left' or 'right'")
        return orientations[new_idx]