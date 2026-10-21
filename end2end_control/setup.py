import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'end2end_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.world')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='inviman',
    maintainer_email='guiller@galileo.edu',
    description='Launch files and worlds for the F1 end-to-end CNN control lab '
                '(Gazebo Harmonic, ROS 2 Jazzy).',
    license='GPL-3.0-only',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'e2e_node = end2end_control.e2e_node:main',
        ],
    },
)
