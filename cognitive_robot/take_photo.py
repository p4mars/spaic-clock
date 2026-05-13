import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


SAVE_DIR = os.path.expanduser('~/photos')
TOPIC = '/gripper_camera/image_raw'


class TakePhoto(Node):
    def __init__(self):
        super().__init__('take_photo')
        os.makedirs(SAVE_DIR, exist_ok=True)
        self.bridge = CvBridge()
        self.latest_frame = None
        self.photo_count = 0

        self.create_subscription(Image, TOPIC, self._image_callback, 10)
        self.get_logger().info(f'Luistert op {TOPIC} — druk Enter om een foto te maken, typ "q" om te stoppen.')

    def _image_callback(self, msg):
        self.latest_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    def save_photo(self):
        if self.latest_frame is None:
            self.get_logger().warn('Nog geen camerabeeld ontvangen.')
            return
        filename = os.path.join(SAVE_DIR, f'photo_{self.photo_count:04d}.jpg')
        cv2.imwrite(filename, self.latest_frame)
        self.photo_count += 1
        self.get_logger().info(f'Foto opgeslagen: {filename}')


def main(args=None):
    rclpy.init(args=args)
    node = TakePhoto()

    import threading
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        while True:
            cmd = input()
            if cmd.strip().lower() == 'q':
                break
            node.save_photo()
    except (KeyboardInterrupt, EOFError):
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
