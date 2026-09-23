from setuptools import find_packages, setup

package_name = 'yolo_tennis_ball'

setup(
    name=package_name,
    version='0.1.0',
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
    description='YOLO tennis-ball training and webcam pixel-coordinate experiment.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'capture_tennis_ball_images = '
            'yolo_tennis_ball.capture_images:main',
            'detect_tennis_ball = yolo_tennis_ball.webcam_detector:main',
            'download_tennis_ball_dataset = '
            'yolo_tennis_ball.download_dataset:main',
            'train_tennis_ball = yolo_tennis_ball.train:main',
        ],
    },
)
