from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'fsm_demo'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Required by ament: registers this package in the ament index
        (
            os.path.join('share', 'ament_index', 'resource_index', 'packages'),
            [os.path.join('resource', package_name)],
        ),
        # Required by ament: package manifest
        (
            os.path.join('share', package_name),
            ['package.xml'],
        ),
        # Install all launch files so `ros2 launch fsm_demo ...` resolves them
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
        # Install all world SDF files so the launch file can find them at runtime
        (
            os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.sdf'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros',
    maintainer_email='ros@todo.todo',
    description='TurtleBot3 FSM obstacle-avoidance demo for Gazebo Harmonic',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # maps `ros2 run fsm_demo fsm_demo_node` → fsm_demo/fsm_demo_node.py:main()
            'fsm_demo_node = fsm_demo.fsm_demo_node:main',
        ],
    },
)