# Ubuntu22.04与ROS2 Humble运行说明

2026-10-15已在本机Ubuntu22.04.5虚拟机完成两包构建、真实ROS通信及Qt虚拟显示自动测试。结果与限制见validation_results.md及evidence/linux。

## 系统准备

推荐原生Ubuntu22.04桌面。WSL2可用Ubuntu22.04与WSLg显示Qt窗口，但监控的是WSL Linux环境，内存和网络受虚拟化影响，不是Windows整机。
安装WSL会修改系统并可能重启，请本人决定。在管理员PowerShell运行 `wsl --install -d Ubuntu-22.04`，重启并配置用户后继续。

## 安装

已通过[官方文档仓库源文件](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Installation/_Apt-Repositories.rst)核验当前使用ros2-apt-source配置密钥与仓库。附带的 `docs/install_humble.sh` 实现UTF-8 locale、universe及ROS仓库配置、系统升级和依赖安装。该脚本已在本次Ubuntu虚拟机执行；新环境仍应先阅读脚本，然后在项目根目录运行 `bash docs/install_humble.sh`。脚本会执行系统升级，请留出安装时间并检查apt输出。

如果已按官方步骤配置好ROS仓库，下面命令也可单独安装所需依赖：

```bash
sudo apt update
sudo apt install ros-humble-desktop ros-dev-tools python3-colcon-common-extensions python3-rosdep python3-psutil python3-pyqt5 python3-pytest
source /opt/ros/humble/setup.bash
# 仅首次初始化，已初始化不重复执行
sudo rosdep init
rosdep update
```

## 构建和测试

复制项目到Linux主目录，例如 `~/unmanned_exam`。WSL尽量不要在 `/mnt/c` 中构建。

```bash
cd ~/unmanned_exam/ros2_workspace
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select status_interfaces status_publisher
source install/setup.bash
ros2 interface show status_interfaces/msg/SystemStatus
colcon test --packages-select status_publisher
colcon test-result --verbose
```

## 运行

每个终端都执行下面两行，保持相同ROS_DOMAIN_ID：

```bash
source /opt/ros/humble/setup.bash
source ~/unmanned_exam/ros2_workspace/install/setup.bash
```

终端1：`ros2 run status_publisher sys_status_pub`

终端2：`ros2 run status_publisher status_gui`

终端3用于验证：

```bash
ros2 topic info /system_status --verbose
ros2 topic echo /system_status --once
ros2 topic hz /system_status
```

默认周期1秒，话题 `/system_status`，可靠QoS深度1。可用 `--ros-args -p period:=0.5` 改变发布周期。GUI数据过期阈值固定3秒，周期大于3秒会出现预期的过期告警。

## 验收和真实证据

把构建输出、接口定义、一次消息、至少10周期的hz结果保存到evidence。GUI应先显示等待，收到后显示8字段及单位；拖动、调整窗口不应卡住；停止发布3秒后显示过期，恢复后接收正常；关闭窗口应退出。截图必须真实抓取，附系统、ROS版本及时间，不要将此流程当作通过记录。

CPU采样与系统监控器的统计窗口可能不同。用 `free -b` 对照内存；available包含可回收页，不等同free。网络是各接口累计发送和接收字节，不能解释为速率。GUI派生速率为相邻计数差除以采样时间差，单位KiB/s；首帧、计数重置和时间回拨显示预热/重置状态。

常见问题：未source、未构建接口、DISPLAY/WSLg不可用、ROS_DOMAIN_ID不一致。GUI以Qt定时器每50ms执行非阻塞spin_once，不创建跨线程控件更新。

可在已配置的Ubuntu中于项目根目录运行 `bash docs/verify_ros2.sh`，保存构建、测试、接口、一次消息与15秒频率输出。脚本不自动判断所有结果，仍需检查hz和GUI交互。频率命令退出124表示预期超时，不代表测试失败或通过。

## 本机Windows可执行验证

项目隔离环境 `.venv` 已安装psutil7.2.2和PyQt5。`python tests/sample_host.py`采集真实Windows主机数据，不通过ROS。
`tests/test_qt_offline.py`只替代ROS导入和传输，运行真实Qt控件和真实采集器。通过PowerShell设置 `$env:QT_QPA_PLATFORM='windows'` 后，用 `.venv/Scripts/python.exe -X utf8 tests/test_qt_offline.py` 执行；结束后 `Remove-Item Env:\QT_QPA_PLATFORM`。测试会短暂显示窗口并保存控件图像，不能代替Humble集成测试。Windows离屏插件此前产生空白图，应使用windows插件验证实际绘制。

本机曾出现Qt默认插件路径把中文目录读成问号；程序在Windows路径无效时按PyQt5真实安装目录修复当前进程的插件路径，不修改系统Qt Creator。无需为此重装Qt Creator，也不能随意拷贝不同版本的qwindows.dll。

## 依赖及接口说明

platform是标准库，不需pip。使用Ubuntu apt的psutil及PyQt5；rclpy来自ROS2，status_interfaces由colcon生成。原题字段类型为示例，保留8个名称，将内存和网络字节从float32改为uint64，避免大累计量精度损失。维护者姓名与邮箱为明确占位，需要本人确认。
