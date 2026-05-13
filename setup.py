from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'cognitive_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mike',
    maintainer_email='mikesmalbroek@hotmail.com',
    description='Cognitive robot package',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'drive_and_arm = cognitive_robot.drive_and_arm:main',
        'take_photo = cognitive_robot.take_photo:main',
        ],
    },
)