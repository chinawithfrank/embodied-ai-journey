from setuptools import find_packages, setup

package_name = 'ros2_fundamentals'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='frank',
    maintainer_email='frank@chinawithfrank.com',
    description='Chapter 01 experiments: turtlesim keyboard teleop, and a pub/sub example.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'keyboard_teleop = ros2_fundamentals.keyboard_teleop:main',
            'pub_example = ros2_fundamentals.pub_example:main',
            'sub_example = ros2_fundamentals.sub_example:main',
        ],
    },
)
