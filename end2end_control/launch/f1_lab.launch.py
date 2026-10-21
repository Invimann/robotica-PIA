#!/usr/bin/env python3
"""
f1_lab.launch.py - F1 car end-to-end control lab (Gazebo Harmonic + ROS 2 Jazzy).

Starts Gazebo with one of the supported circuits, spawns the holonomic F1 car
on the start line and bridges the topics the lab uses:

    /f1/camera/image_raw   sensor_msgs/Image        (Gazebo -> ROS)  your node SUBSCRIBES
    /f1/cmd_vel            geometry_msgs/Twist      (ROS -> Gazebo)  your node PUBLISHES
    /f1/odom               nav_msgs/Odometry        (Gazebo -> ROS)  optional
    /clock                 rosgraph_msgs/Clock      (Gazebo -> ROS)  optional (use_sim_time)

Usage
-----
    ros2 launch end2end_control f1_lab.launch.py world:=simple_circuit
    ros2 launch end2end_control f1_lab.launch.py world:=montmelo_line
    ros2 launch end2end_control f1_lab.launch.py world:=montreal_line
    ros2 launch end2end_control f1_lab.launch.py world:=nurburgring_line

Optional arguments
------------------
    x:= y:= Y:= z:=     override the stored spawn pose (metres / radians)
    gui:=false          run the Gazebo server only (no window)
    spawn_delay:=8.0    seconds to wait for Gazebo to load before spawning
    mode:=holo          car variant forwarded to custom_robots f1.launch.py

How it works
------------
The car itself (xacro, meshes, camera, VelocityControl plugin, bridges) is
NOT re-implemented here: this file includes `f1.launch.py` from the
`custom_robots` package, exactly as RoboticsInfrastructure ships it. What this
package adds is: the world files, the per-world spawn poses
(config/spawn_poses.yaml), GZ_SIM_RESOURCE_PATH, and the /clock bridge.
"""

import os

import yaml
from ament_index_python.packages import (
    PackageNotFoundError,
    get_package_share_directory,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

_PKG = 'end2end_control'


def _share(package):
    """share/<package> directory, with a friendly error if it is missing."""
    try:
        return get_package_share_directory(package)
    except PackageNotFoundError as exc:
        raise RuntimeError(
            f"\n[{_PKG}] ROS package '{package}' not found.\n"
            f"  Did you build the workspace and source it?\n"
            f"    cd ~/ros2_ws && colcon build && source install/setup.bash\n"
        ) from exc


def _load_poses():
    path = os.path.join(_share(_PKG), 'config', 'spawn_poses.yaml')
    with open(path, 'r') as fh:
        return yaml.safe_load(fh)


def _launch_setup(context, *args, **kwargs):
    poses = _load_poses()
    world = LaunchConfiguration('world').perform(context)
    pose = poses['worlds'][world]

    def pick(arg_name, fallback):
        """Launch-argument value if the user gave one, else the YAML value."""
        value = LaunchConfiguration(arg_name).perform(context).strip()
        return value if value else str(fallback)

    x = pick('x', pose['x'])
    y = pick('y', pose['y'])
    yaw = pick('Y', pose['yaw'])
    z = pick('z', poses.get('default_z', 0.1))

    gui = LaunchConfiguration('gui').perform(context).lower() in (
        'true', '1', 'yes')
    spawn_delay = float(LaunchConfiguration('spawn_delay').perform(context))
    mode = LaunchConfiguration('mode').perform(context)

    world_file = os.path.join(_share(_PKG), 'worlds', f'{world}.world')
    if not os.path.isfile(world_file):
        raise FileNotFoundError(f'[{_PKG}] world file not found: {world_file}')

    # GZ_SIM_RESOURCE_PATH must contain custom_robots' models/ folder so that
    # model://<track> in the worlds resolves. Prepend it (if the workspace is
    # sourced the custom_robots hook already did this; doing it again is
    # harmless and makes the launch file independent of that hook).
    cr_models = os.path.join(_share('custom_robots'), 'models')
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    parts = [cr_models] + [
        p for p in existing.split(':') if p and p != cr_models]
    resource_path = ':'.join(parts)

    # -r : start running (unpaused)   -s : server only (no GUI)
    gz_args = f'-r -v4 {world_file}'
    if not gui:
        gz_args = f'-r -s -v4 {world_file}'

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(_share('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': gz_args,
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # Spawn the car with the upstream launch file. Delayed so the world (and
    # its large track meshes) is loaded before the create service is called.
    f1_car = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(_share('custom_robots'), 'launch', 'f1.launch.py')),
        launch_arguments={
            'x': x,
            'y': y,
            'z': z,
            'Y': yaw,
            'mode': mode,
            'sensor': 'camera',
            'use_sim_time': 'true',
        }.items(),
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
    )

    return [
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resource_path),
        LogInfo(msg=(f'[{_PKG}] world={world}  pose: x={x} y={y} z={z} '
                     f'yaw={yaw}  gui={gui}  mode={mode}')),
        gz_sim,
        clock_bridge,
        TimerAction(period=spawn_delay, actions=[f1_car]),
    ]


def generate_launch_description():
    worlds = list(_load_poses()['worlds'].keys())

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value=worlds[0], choices=worlds,
            description='Circuit to load: ' + ' | '.join(worlds)),
        DeclareLaunchArgument(
            'x', default_value='',
            description='Override spawn x (m). Empty = value from spawn_poses.yaml'),
        DeclareLaunchArgument(
            'y', default_value='',
            description='Override spawn y (m). Empty = value from spawn_poses.yaml'),
        DeclareLaunchArgument(
            'z', default_value='',
            description='Override spawn z (m). Empty = default_z from spawn_poses.yaml'),
        DeclareLaunchArgument(
            'Y', default_value='',
            description='Override spawn yaw (rad). Empty = value from spawn_poses.yaml'),
        DeclareLaunchArgument(
            'gui', default_value='true',
            description='Show the Gazebo window (false = server only)'),
        DeclareLaunchArgument(
            'spawn_delay', default_value='6.0',
            description='Seconds to wait for Gazebo to load before spawning the car'),
        DeclareLaunchArgument(
            'mode', default_value='ackermann',
            description='Car variant for custom_robots f1.launch.py (holo | ackermann)'),
        OpaqueFunction(function=_launch_setup),
    ])
