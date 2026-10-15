#!/usr/bin/env bash
# Run from project root on configured Ubuntu22.04/Humble. Real ROS test only.
set -eo pipefail
mkdir -p evidence/linux
source /opt/ros/humble/setup.bash
{
  date --iso-8601=seconds
  cat /etc/os-release
  python3 -c 'import psutil; print("psutil", psutil.__version__)'
} | tee evidence/linux/environment.txt
cd ros2_workspace
colcon build --symlink-install --packages-select status_interfaces status_publisher 2>&1 | tee ../evidence/linux/build.txt
source install/setup.bash
ros2 interface show status_interfaces/msg/SystemStatus | tee ../evidence/linux/interface.txt
colcon test --packages-select status_publisher 2>&1 | tee ../evidence/linux/colcon_test.txt
colcon test-result --verbose 2>&1 | tee ../evidence/linux/test_results.txt
setsid ros2 run status_publisher sys_status_pub > ../evidence/linux/publisher.txt 2>&1 &
publisher_pid=$!
trap 'kill -INT -- -"$publisher_pid" 2>/dev/null || true; wait "$publisher_pid" 2>/dev/null || true' EXIT
timeout 20 ros2 topic echo /system_status --once | tee ../evidence/linux/message.txt
# A timeout is expected after enough samples; other errors must fail the script.
set +e
timeout --signal=INT 15 ros2 topic hz /system_status > ../evidence/linux/hz.txt 2>&1
hz_exit=$?
set -e
if [[ "$hz_exit" != 0 && "$hz_exit" != 124 ]]; then
  cat ../evidence/linux/hz.txt
  exit "$hz_exit"
fi
cat ../evidence/linux/hz.txt
echo 'Inspect hz evidence. GUI still needs manual interactive verification.'
