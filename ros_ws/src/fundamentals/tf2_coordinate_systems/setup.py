from setuptools import find_packages, setup

package_name = 'tf2_coordinate_systems'

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
    description=(
        'Chapter 02 examples for TF2 coordinate frames and transforms.'),
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'static_frame_broadcaster = '
            'tf2_coordinate_systems.static_frame_broadcaster:main',
            'dynamic_frame_broadcaster = '
            'tf2_coordinate_systems.dynamic_frame_broadcaster:main',
            'frame_listener = tf2_coordinate_systems.frame_listener:main',
        ],
    },
)
