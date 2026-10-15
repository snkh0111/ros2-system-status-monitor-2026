"""Qt event loop drives nonblocking ROS callbacks on the GUI thread."""
from datetime import datetime
from pathlib import Path
import sys
import time

from PyQt5.QtCore import QCoreApplication, QLibraryInfo, QTimer
from PyQt5.QtWidgets import QApplication, QFormLayout, QLabel, QWidget
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from status_interfaces.msg import SystemStatus

from .collector import Sample, rates


def configure_qt_plugins():
    """Repair malformed Windows Unicode install paths without changing Qt globally."""
    if sys.platform == 'win32' and not Path(
            QLibraryInfo.location(QLibraryInfo.PluginsPath)).is_dir():
        import PyQt5
        plugins = Path(PyQt5.__file__).resolve().parent / 'Qt5/plugins'
        if plugins.is_dir():
            QCoreApplication.setLibraryPaths([str(plugins)])


class StatusWindow(QWidget):
    """Display latest message; warn on data older than three seconds."""

    def __init__(self, node, executor):
        super().__init__()
        self.setWindowTitle('ROS2 System Status')
        self.resize(520, 340)
        self.executor = executor
        self.previous = None
        self.last_received = None
        layout = QFormLayout(self)
        self.labels = {}
        for key, title in (
            ('stamp', 'Sample time (local)'), ('hostname', 'Hostname'),
            ('cpu', 'CPU usage'), ('memory', 'Memory usage'),
            ('total', 'Total memory'), ('available', 'Available memory'),
            ('sent', 'Sent cumulative'), ('recv', 'Received cumulative'),
            ('rate', 'Sent / received rate'), ('received', 'GUI updated (local)'),
            ('state', 'Status'),
        ):
            label = QLabel('Waiting for message')
            label.setWordWrap(True)
            self.labels[key] = label
            layout.addRow(title, label)
        self.subscription = node.create_subscription(
            SystemStatus, 'system_status', self.receive, 1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(50)

    def receive(self, msg):
        ns = msg.stamp.sec * 1_000_000_000 + msg.stamp.nanosec
        current = Sample(ns, msg.hostname, msg.cpu_percent, msg.memory_percent,
                         msg.memory_total, msg.memory_available, msg.net_sent, msg.net_recv)
        speed = rates(self.previous, current)
        self.previous = current
        self.last_received = time.monotonic()
        values = {
            'stamp': datetime.fromtimestamp(ns / 1e9).isoformat(timespec='milliseconds'),
            'hostname': msg.hostname,
            'cpu': f'{msg.cpu_percent:.1f} %',
            'memory': f'{msg.memory_percent:.1f} %',
            'total': f'{msg.memory_total / 2**30:.3f} GiB ({msg.memory_total} B)',
            'available': f'{msg.memory_available / 2**30:.3f} GiB ({msg.memory_available} B)',
            'sent': f'{msg.net_sent / 2**20:.3f} MiB ({msg.net_sent} B)',
            'recv': f'{msg.net_recv / 2**20:.3f} MiB ({msg.net_recv} B)',
            'rate': ('Warming up / counter or clock reset' if speed is None else
                     f'{speed[0] / 1024:.2f} / {speed[1] / 1024:.2f} KiB/s'),
            'received': datetime.now().isoformat(timespec='milliseconds'),
            'state': 'Receiving',
        }
        for key, value in values.items():
            self.labels[key].setText(value)

    def poll(self):
        if not rclpy.ok():
            self.labels['state'].setText('ROS context stopped')
            self.timer.stop()
            return
        try:
            self.executor.spin_once(timeout_sec=0)
        except Exception as exc:
            self.labels['state'].setText(f'ROS callback error: {exc}')
            return
        if self.last_received is None:
            self.labels['state'].setText('Waiting: check publisher, topic and ROS_DOMAIN_ID')
        elif time.monotonic() - self.last_received > 3.0:
            self.labels['state'].setText('Stale (>3 s): publisher stopped or collection failed')


def main(args=None):
    rclpy.init(args=args)
    configure_qt_plugins()
    app = QApplication(sys.argv[:1])
    node = Node('status_gui')
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    window = StatusWindow(node, executor)
    window.show()
    try:
        app.exec_()
    except KeyboardInterrupt:
        pass
    finally:
        window.timer.stop()
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
