"""
Calibration Constants Module

Manages calibration constants for converting time-based commands
into grid cell movements.
"""

from dataclasses import dataclass


@dataclass
class CalibrationConfig:
    """
    Holds calibration constants for the vacuum robot.

    These constants must be determined through manual calibration:
    - speed_cm_per_sec: Measure how far the robot moves in a set time
    - turn_rate_deg_per_sec: Measure how many degrees it turns in a set time
    - cell_size_cm: Choose based on robot diameter (e.g., 30cm for a 25cm robot)
    """

    speed_cm_per_sec: float = 10.0
    turn_rate_deg_per_sec: float = 90.0
    cell_size_cm: float = 30.0
