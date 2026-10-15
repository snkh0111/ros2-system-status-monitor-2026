# ROS2 Humble 系统状态监控

Ubuntu22.04 + ROS2 Humble两包工程：status_interfaces定义8字段消息，status_publisher采集主机状态并发布，Qt订阅实时显示。

消息包含时间、主机名、CPU%、内存%、总/可用内存字节、累计发送/接收字节。网络累计量与GUI派生速率明确区分，超过3秒无消息时提示过期。

## 安装 构建 运行

完整步骤见[Ubuntu运行说明](docs/ubuntu22_run.md)。新Ubuntu22.04系统先阅读并执行bash docs/install_humble.sh，再执行：

```bash
source /opt/ros/humble/setup.bash
cd ros2_workspace
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select status_interfaces status_publisher
source install/setup.bash
ros2 run status_publisher sys_status_pub
```

另一个终端source同样环境，然后运行ros2 run status_publisher status_gui。
默认1Hz发布；可用--ros-args -p period:=0.5调整发布周期。

## 真实验证状态

5项独立逻辑/结构测试通过；Windows真实Qt控件与真实psutil采集已验证，ROS层为测试替代，不能代替Humble集成。公开日志见evidence。
Ubuntu22.04.5虚拟机已安装，真实Humble构建、通信和GUI验收正在进行。当前不声称这些Linux测试已通过，完成后更新结果。

Linux配置就绪后从项目根目录执行bash docs/verify_ros2.sh保存构建、接口、消息、频率与测试记录；source工作空间后可用xvfb-run -a python3 tests/test_ros2_live.py执行真实ROS+Qt测试。

platform是标准库；psutil、PyQt5、rclpy按Ubuntu/ROS依赖安装。两个包采用MIT许可证，详见各包LICENSE。
