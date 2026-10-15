# 实际验证结果

日期：2026-10-15（北京时间）。目标Ubuntu22.04 / ROS2 Humble；实际Ubuntu22.04.5 VirtualBox虚拟机，1vCPU、4GiB，psutil5.9.0。

两包colcon构建成功，自定义8字段消息能被ROS CLI接收。15秒频率采样显示平均1.000Hz；最新11间隔窗口0.999–1.001秒。证据见evidence/linux的environment.txt、build.txt、interface.txt、message.txt、hz.txt。

真实rclpy节点与psutil、PyQt5控件在Xvfb虚拟显示中运行，接收、派生速率、调整大小、停止发布后过期、恢复、关闭通过。ros2_gui_results.json和两张PNG为真实测试产物，无ROS替代对象。此验收未测长时人工拖动、部署到实车或性能上限。

colcon test实际发现0测试，不记为包内单元测试通过。项目另有5项独立逻辑/结构测试在Windows通过。Linux自动GUI命令为：

```bash
source /opt/ros/humble/setup.bash
source ros2_workspace/install/setup.bash
export ROS_DOMAIN_ID=72
xvfb-run -a python3 tests/test_ros2_live.py
```

需要apt安装xvfb与xauth。首次过期断言失败，原因是CLI验证结束后仍有子发布器；修复verify_ros2.sh的进程组清理后同域重跑通过，未遗留发布器。首次失败日志保留。

安装时rosdep update由于raw.githubusercontent.com TLS超时失败。所需依赖已通过apt安装，所以继续构建并验证，未把rosdep操作标记为成功。新环境仍推荐正常完成rosdep初始化、更新和依赖安装；网络失败时应核对具体缺失依赖，不能无条件忽略错误。
