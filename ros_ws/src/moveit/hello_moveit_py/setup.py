import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'hello_moveit_py'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='frank',
    maintainer_email='frank@chinawithfrank.com',
    description='First MoveItPy planning and execution experiment.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'hello_moveit_py = hello_moveit_py.pose_goal:main',
            'planning_around_objects = '
            'hello_moveit_py.planning_around_objects:main',
            'mtc_pick_place = hello_moveit_py.mtc_pick_place:main',
            'mtc_scene_setup = hello_moveit_py.mtc_scene_setup:main',
            'rviz_visualizer = hello_moveit_py.rviz_visualizer:main',
        ],
    },
)
