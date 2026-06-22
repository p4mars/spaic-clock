#!/usr/bin/env python3
"""
odom_tf_broadcaster.py

Republishes the /odom topic as a odom → base_link TF transform on the laptop.

WHY THIS IS NEEDED
------------------
When running Nav2 on the laptop and the robot over WiFi, the robot's own
TF publisher (odom → base_link) is often not received in time or at all.
This node subscribes to /odom on the laptop side and broadcasts the same
transform locally, so Nav2 always has a fresh odom → base_link TF.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros


class OdomTFBroadcaster(Node):

    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        self._tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.create_subscription(Odometry, '/odom', self._odom_callback, 10)
        self.get_logger().info('odom_tf_broadcaster ready — broadcasting odom → base_link.')

    def _odom_callback(self, msg):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = msg.pose.pose.position.z
        t.transform.rotation = msg.pose.pose.orientation
        self._tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = OdomTFBroadcaster()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
