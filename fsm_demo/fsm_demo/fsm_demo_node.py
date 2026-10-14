#!/usr/bin/env python3
"""
fsm_demo_node.py
================
Reactive obstacle-avoidance node using a 3-state Finite State Machine.


        ┌─────────┐  obstacle     ┌──────┐   2 s    ┌──────┐
        │ FORWARD │ ────────────► │ BACK │ ────────► │ LEFT │
        └─────────┘  detected     └──────┘           └──────┘
              ▲                                         │
              └─────────────────────────────────────────┘
                                 2 s

Subscribes  : /scan      (sensor_msgs/LaserScan)
Publishes   : /cmd_vel   (geometry_msgs/Twist)

Assignment
----------
All TODO blocks below are yours to complete. Do not modify anything outside
them unless you have a good reason and can explain it.

Running the node
----------------
    # Terminal 1 — start the simulation
    ros2 launch fsm_demo sim.launch.py world:=obstacles

    # Terminal 2 — start your node (use_sim_time keeps clocks in sync)
    ros2 run fsm_demo fsm_demo_node --ros-args -p use_sim_time:=true
"""

import math
from enum import Enum, auto

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan


# ── FSM states ────────────────────────────────────────────────────────────────

class State(Enum):
    FORWARD = auto()   # Drive straight ahead (default)
    BACK    = auto()   # Reverse for BACK_DURATION seconds
    LEFT    = auto()   # Rotate left for TURN_DURATION seconds


# ── Tunable constants ─────────────────────────────────────────────────────────
# Adjust these values to change how the robot behaves.
# Units: metres, metres/second, radians/second, seconds.

FORWARD_SPEED       = 0.15    # linear.x while going forward  [m/s]
BACK_SPEED          = 0.10    # linear.x magnitude while reversing (published negative)
TURN_SPEED          = 0.50    # angular.z while rotating left  [rad/s]

BACK_DURATION       = 2.0     # how long to stay in BACK  [s]
TURN_DURATION       = 2.0     # how long to stay in LEFT  [s]

# If the closest ray in the forward sector is nearer than this, the FSM
# transitions FORWARD → BACK. Tune this so the robot reacts early enough
# to avoid actually hitting the obstacle.
OBSTACLE_THRESHOLD  = 0.50    # [m]  ← TODO: tune me (after your lab is working)


# ── Node ──────────────────────────────────────────────────────────────────────

class FsmDemoNode(Node):
    """3-state FSM obstacle-avoidance node for the fsm_demo lab."""

    def __init__(self):
        super().__init__('fsm_demo_node')
        #── STEP 0 ── Create the publishers and subscribers ────────
        #TODO: create a publisher for /cmd_vel (Twist) and a subscriber for /scan (LaserScan) using self.create_publisher() and self.create_subscription().
        #go check the ROS2 documentation for the correct syntax and parameters for these methods.
        self._cmd_pub = ...
        self._scan_sub = ...

        # ── Internal state ────────────────────────────────────────────────
        self._state: State = State.FORWARD
        self._latest_scan: LaserScan | None = None
        # Records the time when the current state was entered.
        # Used to measure how long the robot has been in BACK or LEFT.
        self._state_start_time = self.get_clock().now()

        # ── FSM timer ─────────────────────────────────────────────────────
        # Fires at 10 Hz. All FSM logic runs inside _timer_callback.
        self._timer = self.create_timer(0.1, self._timer_callback)

        self.get_logger().info(
            'FsmDemoNode ready — waiting for first /scan message …'
        )

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _scan_callback(self, msg: LaserScan) -> None:
        """Store the latest LaserScan so the FSM timer can read it."""
        self._latest_scan = msg

    def _timer_callback(self) -> None:
        """
        Main FSM loop — called at 10 Hz.

        LaserScan quick-reference
        ─────────────────────────
        self._latest_scan.ranges    : tuple[float, ...]  (360 values for TB3 Burger)
        self._latest_scan.range_min : minimum valid range  ≈ 0.12 m
        self._latest_scan.range_max : maximum valid range  ≈ 3.50 m

        Index layout (bird's-eye view, robot faces ↑):

                         0  (forward)
                    330 ╱│╲ 30
                  315  ╱ │ ╲  45
                      ╱  │  ╲
             270 ────────┼──────── 90
                      ╲  │  ╱
                  225  ╲ │ ╱  135
                        ╲│╱ (backward)
                        180

        Values of `inf` mean the ray hit nothing within range_max.
        Values of `nan` are rare but can appear — both must be filtered out
        before calling min(), otherwise min() returns nan silently.

        Useful checks:
            math.isinf(v)   →  True if v is ±inf
            math.isnan(v)   →  True if v is nan
        """

        # Guard — do nothing until the first scan has arrived.
        if self._latest_scan is None:
            return

        # ── STEP 1 ── Find the minimum range in the forward sector ────────
        #
        # The forward sector spans roughly ±30° around index 0.
        # That means indices 0–30  AND  indices 330–359.
        #
        # TODO:
        #   1. Build a list of the range values for those indices. Remember, 
        #   indices 0-30 and 330-359 represent the front of the robot.
        #   use self._latest_scan.ranges to access the ranges.
        #   2. Remove any values that are inf or nan (they mean "no obstacle").
        #   3. If the filtered list is empty (no valid readings at all), treat
        #      it as no obstacle — set min_front_dist = float('inf').
        #   4. Otherwise set min_front_dist = min(filtered list).
        
        
        
        scan_list = ...
        filtered_list = ...


        #   check if the filtered list has a value lower than the OBSTACLE_THRESHOLD, 
        #   if so, set min_front_dist to that value, otherwise set it to float('inf')
        
        
        min_front_dist = ...   # ← replace with your implementation

        # ── STEP 2 ── FORWARD state ───────────────────────────────────────
        if self._state == State.FORWARD:
            #
            # TODO:
            #   • If min_front_dist < OBSTACLE_THRESHOLD:
            #       - Stop the robot immediately (hint: self._stop()).
            #       - Transition to State.BACK (hint: self._transition_to(…)).
            #   • Otherwise:
            #       - Publish a Twist that drives the robot forward at
            #         FORWARD_SPEED with no rotation.
            #         (hint: self._publish_velocity(linear_x, angular_z))
            pass

        # ── STEP 3 ── BACK state ──────────────────────────────────────────
        elif self._state == State.BACK:
            #
            # TODO:
            #   • Publish a Twist that drives the robot backward.
            #     Remember: negative linear.x = reverse.
            #   • Compute how many seconds have elapsed since entering this state:
            #
            #       elapsed = (self.get_clock().now()
            #                  - self._state_start_time).nanoseconds * 1e-9
            #
            #   • If elapsed >= BACK_DURATION, transition to State.LEFT.
            pass

        # ── STEP 4 ── LEFT state ──────────────────────────────────────────
        elif self._state == State.LEFT:
            #
            # TODO:
            #   • Publish a Twist that rotates the robot to the left.
            #     Remember: positive angular.z = counter-clockwise = left.
            #   • Compute elapsed time the same way as in STEP 3.
            #   • If elapsed >= TURN_DURATION, transition to State.FORWARD.
            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _publish_velocity(self, linear_x: float, angular_z: float) -> None:
        """Build and publish a Twist message. Both arguments default to 0."""
        msg = Twist()
        msg.linear.x  = float(linear_x)
        msg.angular.z = float(angular_z)
        self._cmd_pub.publish(msg)

    def _stop(self) -> None:
        """Publish zero velocity — stops the robot in place."""
        self._publish_velocity(0.0, 0.0)

    def _transition_to(self, new_state: State) -> None:
        """
        Switch to a new FSM state.

        Resets the state clock and logs the transition so you can see
        exactly when and why the FSM changes state.
        You don't need to modify this — just call it:
            self._transition_to(State.BACK)
        """
        self.get_logger().info(
            f'FSM transition: {self._state.name} → {new_state.name}'
        )
        self._state = new_state
        self._state_start_time = self.get_clock().now()


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None) -> None:
    rclpy.init(args=args)
    node = FsmDemoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._stop()          # leave the robot stationary on exit
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()