from setuptools import setup
import os
from glob import glob
from setuptools import setup

package_name = 'artiv_imu_driver'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Junsang Ryu',
    maintainer_email='js52065@dgist.ac.kr',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'imu_driver_node = artiv_imu_driver.imu_driver_node:main'
        ],
    },
)
