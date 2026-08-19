import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'web_gateway_demo'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='frank',
    maintainer_email='frank@chinawithfrank.com',
    description='Demo ROS graph for the ROS2 Web Gateway v0.1.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'rotation_server = web_gateway_demo.rotation_server:main',
        ],
    },
)
