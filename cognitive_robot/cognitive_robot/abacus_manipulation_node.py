#!/usr/bin/env python3
"""
abacus_manipulation_node.py

ROS2 service node that controls the MIRTE Master arm to place rings on the
abacus (Station B).  The master node (station_demo.py) calls /abacus/run_sequence
with the four time digits read at Station A.

Services offered:
    /abacus/run_sequence  (cognitive_robot_interfaces/srv/RunAbacus)
        Start the full placement sequence.  Blocks until complete.

Usage (standalone test):
    ros2 run cognitive_robot abacus_manipulation_node

Trigger sequence from master node or test terminal:
    ros2 service call /abacus/run_sequence \\
        cognitive_robot_interfaces/srv/RunAbacus "{time_digits: [1, 2, 1, 2]}"
"""

import math
import time

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

from cognitive_robot_interfaces.srv import RunAbacus

# ── Joint angle constants — tune these on the real robot (radians) ────────────
SHOULDER_LIFT_WORK    =  0.0   # shoulder lift at working height
WRIST_WORK            =  0.0   # wrist kept level throughout

ELBOW_TRANSIT         =  0.0   # arm fully upright — safe to rotate between poles
ELBOW_RECEIVE         = -0.7   # arm slightly raised (~40°) — ring is placed here
ELBOW_WORK            = -1.57  # elbow 90° forward — hover above pole
SHOULDER_LIFT_TRANSIT = -0.8  # shoulder dips to slide ring off onto the pole

# Seconds the controller has to reach each target position before we move on
MOVE_SEC = 2

# ── Timing constants (seconds) ────────────────────────────────────────────────
ARRIVE_WAIT_SEC  = 2.0   # pause after arriving at Station B before starting
RING_PLACE_SEC   = 2.0   # time at receive position for ring placement
LOWER_PAUSE_SEC  = 1.5   # pause after lowering to 90° before dipping shoulder
RELEASE_HOLD_SEC = 1.5   # time held at dipped (release) position
RETURN_PAUSE_SEC = 1.5   # pause after shoulder returns to working height
# ─────────────────────────────────────────────────────────────────────────────

# Shoulder pan angle for each of the four poles, measured from centre
POLE_PAN_ANGLES = [
    math.radians( 28),  # pole 1 — far left
    math.radians( 10),  # pole 2 — slight left
    math.radians(-10),  # pole 3 — slight right
    math.radians(-28),  # pole 4 — far right
]


class AbacusManipulationNode(Node):
    """
    Controls the MIRTE arm to place rings on the abacus poles.

    The sequence is driven by a list of four digits (e.g. [1, 4, 3, 2])
    where each digit is the number of rings to place on the corresponding pole.
    """

    def __init__(self):
        super().__init__('abacus_manipulation_node')

        # Publisher that sends joint trajectories to the arm controller
        self._arm_pub = self.create_publisher(
            JointTrajectory,
            '/mirte_master_arm_controller/joint_trajectory',
            10,
        )

        # Service that the master node calls to start the full placement sequence
        self.create_service(RunAbacus, '/abacus/run_sequence', self._on_run_sequence)

        self.get_logger().info('Abacus manipulation node ready.')
        self.get_logger().info('  Waiting for /abacus/run_sequence call...')

    # ── Service callback ─────────────────────────────────────────────────────

    def _on_run_sequence(self, request, response):
        """Called by the master node. Blocks until the full sequence is done."""
        digits = list(request.time_digits)
        self.get_logger().info(f'run_sequence called with digits: {digits}')
        self._run_sequence(digits)
        response.success = True
        return response

    # ── Arm movement helper ──────────────────────────────────────────────────

    def _move_arm(self, pan, lift, elbow, wrist):
        """
        Send a single joint trajectory goal and block until the motion completes.

        Args:
            pan:   shoulder_pan_joint   — left/right rotation (rad)
            lift:  shoulder_lift_joint  — shoulder up/down (rad)
            elbow: elbow_joint          — elbow bend (rad)
            wrist: wrist_joint          — wrist angle (rad)
        """
        msg = JointTrajectory()
        msg.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_joint',
        ]

        pt = JointTrajectoryPoint()
        pt.positions = [pan, lift, elbow, wrist]
        pt.time_from_start = Duration(sec=MOVE_SEC, nanosec=0)
        msg.points.append(pt)

        self._arm_pub.publish(msg)

        # Wait for the controller to reach the target before continuing
        time.sleep(MOVE_SEC + 0.3)

    # ── Sequence logic ───────────────────────────────────────────────────────

    def _run_sequence(self, time_digits):
        """
        Full ring-placement sequence for one abacus reading.

        Sequence per ring:
            1. Receive position (ELBOW_RECEIVE) — wait RING_PLACE_SEC for ring placement.
            2. Lower to working height (ELBOW_WORK) — pause LOWER_PAUSE_SEC.
            3. Dip shoulder (SHOULDER_LIFT_TRANSIT) — hold RELEASE_HOLD_SEC.
            4. Return shoulder to working height — pause RETURN_PAUSE_SEC.
            5. Repeat from 1 for next ring, or raise to transit for next pole.

        Args:
            time_digits: list of four ints, e.g. [1, 4, 3, 2]
        """
        self.get_logger().info(f'Starting abacus sequence — digits: {time_digits}')

        # Wait for alignment after arriving at Station B
        self.get_logger().info(f'Waiting {ARRIVE_WAIT_SEC:.0f} s for alignment...')
        time.sleep(ARRIVE_WAIT_SEC)

        # Start upright at centre so first rotation is safe
        self._move_arm(0.0, SHOULDER_LIFT_WORK, ELBOW_TRANSIT, WRIST_WORK)

        for pole_idx, count in enumerate(time_digits):
            pan = POLE_PAN_ANGLES[pole_idx]
            self.get_logger().info(
                f'Pole {pole_idx + 1}/4  |  pan={math.degrees(pan):.0f}°  |  rings={count}'
            )

            # Rotate to pole while arm is fully upright — avoids knocking poles
            self._move_arm(pan, SHOULDER_LIFT_WORK, ELBOW_TRANSIT, WRIST_WORK)

            # Lower to working height above the pole
            self._move_arm(pan, SHOULDER_LIFT_WORK, ELBOW_WORK, WRIST_WORK)

            for i in range(count):
                self.get_logger().info(f'  Ring {i + 1}/{count}')

                # Raise to receive position — wait for ring to be placed
                self._move_arm(pan, SHOULDER_LIFT_WORK, ELBOW_RECEIVE, WRIST_WORK)
                time.sleep(RING_PLACE_SEC)

                # Lower to 90° working height above pole — pause so motion is visible
                self._move_arm(pan, SHOULDER_LIFT_WORK, ELBOW_WORK, WRIST_WORK)
                time.sleep(LOWER_PAUSE_SEC)

                # Dip shoulder to slide ring onto pole — hold so ring settles
                self._move_arm(pan, SHOULDER_LIFT_TRANSIT, ELBOW_WORK, WRIST_WORK)
                time.sleep(RELEASE_HOLD_SEC)

                # Return shoulder to working height — pause before next ring
                self._move_arm(pan, SHOULDER_LIFT_WORK, ELBOW_WORK, WRIST_WORK)
                time.sleep(RETURN_PAUSE_SEC)

            # Raise back to transit before rotating to the next pole
            self._move_arm(pan, SHOULDER_LIFT_WORK, ELBOW_TRANSIT, WRIST_WORK)

        # Return arm to neutral home position
        self._move_arm(0.0, 0.0, 0.0, 0.0)
        self.get_logger().info('Abacus sequence complete.')


def main(args=None):
    rclpy.init(args=args)
    node = AbacusManipulationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
