#!/usr/bin/env bash
# Setup from official ROS2 Humble documentation. Not run on the Windows host.
# Review before executing on Ubuntu22.04. Network and sudo are required.
set -euo pipefail
. /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_ID" != 22.04 ]]; then
  echo 'This project targets Ubuntu 22.04 only.' >&2
  exit 1
fi
sudo apt update
sudo apt install -y locales software-properties-common curl
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
sudo add-apt-repository -y universe
ROS_APT_SOURCE_VERSION=$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
curl -fL -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${UBUNTU_CODENAME:-${VERSION_CODENAME}}_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
# Official guide recommends upgrading systemd/udev before ROS installation.
sudo apt upgrade -y
sudo apt install -y ros-humble-desktop ros-dev-tools python3-colcon-common-extensions python3-rosdep python3-psutil python3-pyqt5 python3-pytest
echo 'Installed packages. Next: source /opt/ros/humble/setup.bash'
