#!/usr/bin/env python3
"""
End-to-end visual control node (student skeleton).

ROS 2 port of the RoboticsAcademy "End to End Visual Control" exercise
skeleton. HAL.getImage() / HAL.setV() / HAL.setW() are replaced by a
subscriber and a publisher:

    subscribes  /f1/camera/image_raw   sensor_msgs/msg/Image
    publishes   /f1/cmd_vel            geometry_msgs/msg/Twist
                                       (linear.x = v, angular.z = w)

What is already done for you: topics, QoS, and loading the ONNX model with
the CUDA execution provider (falling back to CPU).

What is up to you: everything inside `image_callback`, i.e. converting the
image, preprocessing it the way your network expects, running the model and
publishing v and w.

Run (after `colcon build` and `source install/setup.bash`, with the lab
launch file already running):

    ros2 run end2end_control e2e_node --ros-args -p model_path:=/path/to/model.onnx
"""

import sys

import onnxruntime
import numpy as np
import rclpy
from PIL import Image
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

PROVIDERS = ['CUDAExecutionProvider', 'CPUExecutionProvider']
# PROVIDERS = ['CPUExecutionProvider']


class EndToEndControlNode(Node):

    def __init__(self):
        super().__init__('e2e_control_node')

        self.declare_parameter('model_path', '')
        self.declare_parameter('image_topic', '/f1/camera/image_raw')
        self.declare_parameter('cmd_vel_topic', '/f1/cmd_vel')

        model_path = self.get_parameter('model_path').value
        image_topic = self.get_parameter('image_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value

        self.session = self.load_model_session(model_path)

        self.cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.image_sub = self.create_subscription(
            Image, image_topic, self.image_callback, qos_profile_sensor_data)

        self.get_logger().info(
            f'Subscribed to {image_topic}, publishing on {cmd_vel_topic}')

    def load_model_session(self, model_path):
        if not model_path:
            self.get_logger().fatal(
                "Parameter 'model_path' is empty. Run with "
                '--ros-args -p model_path:=/path/to/model.onnx')
            sys.exit(1)

        if hasattr(onnxruntime, 'preload_dlls'):
            onnxruntime.preload_dlls()

        try:
            session = onnxruntime.InferenceSession(
                model_path, providers=PROVIDERS)
        except Exception as e:
            self.get_logger().fatal(f"Model couldn't be loaded: {e}")
            sys.exit(1)

        self.get_logger().info(
            f'Loaded {model_path} with providers: {session.get_providers()}')
        return session

    def publish_cmd(self, v, w):
        msg = Twist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)
        self.cmd_pub.publish(msg)

    def image_callback(self, msg):
        # TODO:
        #   1. Convert `msg` (sensor_msgs/Image, 640x480, encoding rgb8)
        #      to an array.
        #   2. Preprocess it as your network expects.
        #   3. Run self.session and get v, w.
        #   4. self.publish_cmd(v, w)
        self.publish_cmd(0.0,0.0)


def main(args=None):
    rclpy.init(args=args)
    node = EndToEndControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
