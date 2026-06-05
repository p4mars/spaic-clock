from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package='cognitive_robot',
            executable='detect_abacus_service',
            name='detect_abacus_service',
        ),

        Node(
            package='cognitive_robot',
            executable='detect_station_service',
            name='detect_station_service',
        ),

        Node(
            package='cognitive_robot',
            executable='read_time_service',
            name='read_time_service',
        ),

    ])
