import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'rosbag2_fundamentals'

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
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='frank',
    maintainer_email='frank@chinawithfrank.com',
    description='Fundamentals rosbag2 recording and replay experiment.',
    license='MIT',
    tests_require=['pytest'],
)
