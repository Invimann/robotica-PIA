#!/usr/bin/env python3
"""
sim.launch.py — TurtleBot3 Burger + Gazebo Harmonic launcher for fsm_demo.

Usage
-----
    ros2 launch fsm_demo sim.launch.py                    # default: obstacles
    ros2 launch fsm_demo sim.launch.py world:=empty
    ros2 launch fsm_demo sim.launch.py world:=corridor
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


# ---------------------------------------------------------------------------
# Package share directories — resolved once at import time.
# If a package is missing, get_package_share_directory() raises here with a
# clear message rather than silently failing later.
# ---------------------------------------------------------------------------
_PKG_FSM_DEMO = get_package_share_directory('fsm_demo')
_PKG_ROS_GZ   = get_package_share_directory('ros_gz_sim')
_PKG_TB3_GZ   = get_package_share_directory('turtlebot3_gazebo')
_PKG_TB3_DESC = get_package_share_directory('turtlebot3_description')

# Paths to TB3 Burger assets.
# If your installed version differs, run:
#   find /opt/ros/jazzy -name "model.sdf" | grep burger
#   find /opt/ros/jazzy -name "*.urdf"    | grep burger
_TB3_MODEL_SDF = os.path.join(
    _PKG_TB3_GZ, 'models', 'turtlebot3_burger', 'model.sdf'
)
_TB3_URDF = os.path.join(
    _PKG_TB3_DESC, 'urdf', 'turtlebot3_burger.urdf'
)


# ---------------------------------------------------------------------------
# OpaqueFunction — called at launch time with the fully-resolved context.
# Anything that needs an evaluated LaunchConfiguration value goes here.
# ---------------------------------------------------------------------------
def _launch_setup(context, *args, **kwargs):

    world_name = LaunchConfiguration('world').perform(context)
    world_sdf  = os.path.join(_PKG_FSM_DEMO, 'worlds', f'{world_name}.sdf')

    if not os.path.isfile(world_sdf):
        raise FileNotFoundError(
            f'\n[fsm_demo] World SDF not found: {world_sdf}'
            f'\n  Valid choices: empty | obstacles | corridor'
        )

    # ── Gazebo Harmonic ────────────────────────────────────────────────────
    # -r  starts the simulation immediately (unpaused).
    # on_exit_shutdown brings down the whole launch when the gz window closes.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(_PKG_ROS_GZ, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'-r {world_sdf}',
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # ── Spawn TB3 Burger ───────────────────────────────────────────────────
    # Spawning from the SDF file (not from /robot_description) preserves the
    # Gazebo-specific diff_drive and lidar plugins exactly as TB3 ships them.
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_turtlebot3',
        arguments=[
            '-name', 'turtlebot3_burger',
            '-file', _TB3_MODEL_SDF,
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.01',   # tiny lift prevents ground-collision at t=0
            '-Y', '0.0',    # yaw in radians — robot faces +x (east)
        ],
        output='screen',
    )

    return [
        gz_sim,
        # Delay spawn until Gazebo has loaded the world.
        # 3 s is conservative; fast machines may only need 1–2 s.
        TimerAction(period=3.0, actions=[spawn_robot]),
    ]


# ---------------------------------------------------------------------------
# generate_launch_description
# ---------------------------------------------------------------------------
def generate_launch_description():

    # ── Environment variables ──────────────────────────────────────────────
    # Both must be set before any Gazebo process starts.

    set_tb3_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value='burger',
    )

    # GZ_SIM_RESOURCE_PATH is the Gazebo Harmonic equivalent of
    # GAZEBO_MODEL_PATH. Points Gazebo at the TB3 mesh/model assets.
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(_PKG_TB3_GZ, 'models'),
    )

    # ── Launch arguments ───────────────────────────────────────────────────
    world_arg = DeclareLaunchArgument(
        name='world',
        default_value='obstacles',
        choices=['empty', 'obstacles', 'corridor'],
        description=(
            'Gazebo world to load. '
            'Choices: empty | obstacles | corridor. '
            'SDF files live in share/fsm_demo/worlds/.'
        ),
    )

    # ── robot_state_publisher ──────────────────────────────────────────────
    # Reads the TB3 URDF and publishes /tf (map→odom→base_footprint→…).
    # This is separate from the spawned SDF — it is only used for TF and
    # rviz2 visualisation, not for the Gazebo simulation itself.
    with open(_TB3_URDF, 'r') as fh:
        robot_description = fh.read()

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    # ── ROS ↔ Gazebo topic bridge ──────────────────────────────────────────
    # Bridge string format:  <ros_topic>@<ros_type>{dir}gz.<gz_type>
    #   [  =  gz publishes  → ros subscribes
    #   ]  =  ros publishes → gz subscribes
    #   @  =  bidirectional
    #
    # Required for the FSM lab:   /cmd_vel  /scan  /clock
    # Nice-to-have for debugging: /odom  /tf
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        arguments=[
            # Simulation clock — required for use_sim_time to work correctly
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',

            # Drive commands: FSM node publishes here → diff_drive plugin reads it
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',

            # 2D lidar scan: TB3 sensor → FSM node  ← the core of the lab
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',

            # Odometry from diff_drive plugin (useful for rviz2 / sanity checks)
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',

            # TF from Gazebo: publishes the odom → base_footprint transform
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        # 1. Environment variables — must come before Gazebo starts
        set_tb3_model,
        set_gz_resource_path,

        # 2. Argument declarations
        world_arg,

        # 3. Static nodes (no dependency on launch arg values)
        robot_state_publisher,
        ros_gz_bridge,

        # 4. World-dependent actions (Gazebo + spawn), resolved at launch time
        OpaqueFunction(function=_launch_setup),
    ])