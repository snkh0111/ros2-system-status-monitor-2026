"""Real ROS2 + Qt test, only run in configured Ubuntu/Humble. No ROS doubles."""
from datetime import datetime
import json
from pathlib import Path
import sys

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from status_publisher.status_gui import StatusWindow
from status_publisher.sys_status_pub import SysStatusPub

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'evidence/linux'
out.mkdir(parents=True, exist_ok=True)
rclpy.init()
app = QApplication([])
publisher = SysStatusPub()
subscriber = Node('status_gui_integration_test')
executor = SingleThreadedExecutor()
executor.add_node(publisher)
executor.add_node(subscriber)
window = StatusWindow(subscriber, executor)
window.setWindowTitle('Ubuntu 22.04 / ROS2 Humble / actual ROS messages')
try:
    window.show()
    QTest.qWait(2800)
    assert window.last_received is not None, 'No actual ROS2 message received'
    assert window.labels['state'].text() == 'Receiving'
    assert 'KiB/s' in window.labels['rate'].text()
    window.resize(760, 430)
    QTest.qWait(200)
    assert window.grab().save(str(out / 'ros2_gui_receiving.png'))
    publisher.timer.cancel()
    QTest.qWait(3500)
    assert window.labels['state'].text().startswith('Stale')
    assert window.grab().save(str(out / 'ros2_gui_stale.png'))
    publisher.timer.reset()
    QTest.qWait(1500)
    assert window.labels['state'].text() == 'Receiving'
    window.close()
    app.processEvents()
    assert not window.isVisible()
    result = {'recorded_at': datetime.now().astimezone().isoformat(),
              'scope': 'Actual Humble publisher/subscriber, actual psutil and Qt',
              'checks': ['ROS2 message reception', 'derived rate', 'resize',
                         'publisher timer stop/stale', 'restart/recovery', 'close'],
              'result': 'PASS',
              'limitation': 'Automated virtual display; not long-duration manual latency evaluation'}
    (out / 'ros2_gui_results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
finally:
    window.timer.stop()
    executor.shutdown()
    subscriber.destroy_node()
    publisher.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
