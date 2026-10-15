from setuptools import find_packages, setup

package_name = 'status_publisher'
setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'LICENSE']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Project maintainer pending confirmation',
    maintainer_email='maintainer@example.invalid',
    description='ROS2 system status publisher and Qt GUI',
    license='MIT',
    entry_points={'console_scripts': [
        'sys_status_pub = status_publisher.sys_status_pub:main',
        'status_gui = status_publisher.status_gui:main',
    ]},
)
