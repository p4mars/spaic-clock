import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time


class DriveAndArm(Node):
    def __init__(self):
        super().__init__('drive_and_arm')

        # Publisher voor rijden
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/mirte_base_controller/cmd_vel_unstamped',
            10
        )

        # Publisher voor arm
        self.arm_pub = self.create_publisher(
            JointTrajectory,
            '/mirte_master_arm_controller/joint_trajectory',
            10
        )

        # Timer die na 2 seconden begint (zodat alles verbonden is)
        self.get_logger().info('Wacht even op verbinding...')
        self.create_timer(2.0, self.start_sequence)
        self.sequence_started = False

    def start_sequence(self):
        # Zorgt dat dit maar 1x wordt uitgevoerd
        if self.sequence_started:
            return
        self.sequence_started = True

        self.get_logger().info('Start: rondje rijden!')
        self.drive_circle()

        self.get_logger().info('Arm omhoog!')
        self.move_arm_up()

        self.get_logger().info('Klaar!')

    def drive_circle(self):
        msg = Twist()
        msg.linear.x = 0.2   # vooruit
        msg.angular.z = 0.5  # draaien = samen een rondje

        start = time.time()
        while time.time() - start < 8.0:  # ~8 seconden = 1 rondje
            self.cmd_vel_pub.publish(msg)
            time.sleep(0.1)

        # Stop de robot
        self.cmd_vel_pub.publish(Twist())
        self.get_logger().info('Rondje klaar, robot gestopt.')

    def move_arm_up(self):
        msg = JointTrajectory()
        msg.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_joint'
        ]

        point = JointTrajectoryPoint()
        point.positions = [0.0, 0.0, -1.56, 1.56]  # arm omhoog
        point.time_from_start = Duration(sec=3, nanosec=0)

        msg.points = [point]
        self.arm_pub.publish(msg)
        time.sleep(4)  # wacht tot arm klaar is


def main(args=None):
    rclpy.init(args=args)
    node = DriveAndArm()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()