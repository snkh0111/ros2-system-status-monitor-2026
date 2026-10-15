"""Real Qt rendering with real Windows samples; ROS transport is a test double."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import ModuleType, SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ros2_workspace/src/status_publisher'))

# Only the ROS imports are replaced. This is explicitly not ROS integration.
rclpy = ModuleType('rclpy')
rclpy.ok = lambda: True
sys.modules['rclpy'] = rclpy
for name in ('rclpy.executors', 'rclpy.node', 'status_interfaces', 'status_interfaces.msg'):
    sys.modules[name] = ModuleType(name)
sys.modules['rclpy.executors'].SingleThreadedExecutor = object
sys.modules['rclpy.node'].Node = object
sys.modules['status_interfaces.msg'].SystemStatus = SimpleNamespace

from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtTest import QTest
import PyQt5
from status_publisher.status_gui import StatusWindow, configure_qt_plugins
from status_publisher.collector import Collector


class FakeExecutor:
    def __init__(self):
        self.poll_count = 0

    def spin_once(self, timeout_sec):
        assert timeout_sec == 0
        self.poll_count += 1


class FakeNode:
    def create_subscription(self, message_type, topic, callback, qos):
        assert topic == 'system_status' and qos == 1
        return callback


def as_message(sample):
    sec, nanosec = divmod(sample.stamp_ns, 1_000_000_000)
    return SimpleNamespace(stamp=SimpleNamespace(sec=sec, nanosec=nanosec),
                           **{k: v for k, v in vars(sample).items() if k != 'stamp_ns'})


# This Windows runtime reported ????? in Qt's default Unicode plugin path.
# Use an explicit QString path instead of the malformed installation path.
configure_qt_plugins()
app = QApplication([])
# Offscreen Windows tests need a platform-independent painting style.
app.setStyle('Fusion')
executor = FakeExecutor()
window = StatusWindow(FakeNode(), executor)
window.layout().addRow(QLabel('Windows + real psutil / ROS transport is a TEST DOUBLE'))
window.setWindowTitle('Windows Qt test / real psutil / ROS transport stub')
window.show()
app.processEvents()
window.poll()
assert window.labels['state'].text().startswith('Waiting')
collector = Collector()
time.sleep(0.2)
window.receive(as_message(collector.sample()))
assert window.labels['state'].text() == 'Receiving'
assert 'GiB' in window.labels['total'].text()
assert 'B)' in window.labels['sent'].text()
assert 'Warming up' in window.labels['rate'].text()
time.sleep(0.2)
window.receive(as_message(collector.sample()))
assert 'KiB/s' in window.labels['rate'].text()
window.resize(640, 410)
app.processEvents()
QTest.qWait(150)
print('Label geometry:', window.labels['cpu'].geometry().getRect(),
      'visible:', window.labels['cpu'].isVisible(), flush=True)
assert window.grab().save(str(ROOT / 'evidence/qt_windows_sample.png'))
window.last_received = time.monotonic() - 3.1
window.poll()
assert window.labels['state'].text().startswith('Stale')
app.processEvents()
QTest.qWait(150)
assert window.grab().save(str(ROOT / 'evidence/qt_windows_stale.png'))
window.receive(as_message(collector.sample()))
assert window.labels['state'].text() == 'Receiving'
window.timer.stop()
window.close()
app.processEvents()
assert not window.isVisible()
assert executor.poll_count >= 2
result = {
    'scope': 'Real PyQt5 window + real psutil Windows samples; ROS test doubles',
    'platform_plugin': os.environ['QT_QPA_PLATFORM'],
    'checks': ['waiting', 'all field rendering', 'units', 'initial rate',
               'subsequent rate', 'resize', 'stale state', 'resume', 'close'],
    'result': 'PASS', 'poll_count': executor.poll_count,
    'limitation': 'Not ROS2 discovery, transport, colcon, or interactive latency verification',
}
(ROOT / 'evidence/qt_offline_results.json').write_text(
    json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
