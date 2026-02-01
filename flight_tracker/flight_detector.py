"""
Flight Detector
Automatically detects when a flight starts and ends based on speed
"""

import time


class FlightDetector:
    def __init__(self):
        # Flight detection thresholds
        self.start_speed = 5.0      # mph - speed to trigger flight start
        self.end_speed = 2.0        # mph - speed to trigger flight end
        self.start_duration = 5     # seconds above start_speed to confirm start
        self.end_duration = 30      # seconds below end_speed to confirm end

        # State tracking
        self.in_flight = False
        self.speed_above_start_since = None
        self.speed_below_end_since = None

    def update(self, speed):
        """
        Update flight status based on current speed.
        Returns: 'started', 'ended', or None
        """
        current_time = time.time()

        if not self.in_flight:
            # Not in flight - check for takeoff
            if speed >= self.start_speed:
                if self.speed_above_start_since is None:
                    self.speed_above_start_since = current_time

                # Check if we've been above threshold long enough
                if current_time - self.speed_above_start_since >= self.start_duration:
                    self.in_flight = True
                    self.speed_above_start_since = None
                    self.speed_below_end_since = None
                    return 'started'
            else:
                # Reset counter if speed drops below threshold
                self.speed_above_start_since = None

        else:
            # In flight - check for landing
            if speed <= self.end_speed:
                if self.speed_below_end_since is None:
                    self.speed_below_end_since = current_time

                # Check if we've been below threshold long enough
                if current_time - self.speed_below_end_since >= self.end_duration:
                    self.in_flight = False
                    self.speed_below_end_since = None
                    self.speed_above_start_since = None
                    return 'ended'
            else:
                # Reset counter if speed goes above threshold
                self.speed_below_end_since = None

        return None

    def reset(self):
        """Reset the detector state"""
        self.in_flight = False
        self.speed_above_start_since = None
        self.speed_below_end_since = None
