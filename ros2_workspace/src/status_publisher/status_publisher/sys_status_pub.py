"""Publish host status at a configurable fixed period."""
import math

import rclpy
from rclpy.node import Node
from status_interfaces.msg import SystemStatus

from .collector import Collector


class SysStatusPub(Node):
    """The collector is sampled without a blocking CPU measurement."""

    def __init__(self):
        super().__init__('sys_status_pub')
        period = float(self.declare_parameter('period', 1.0).value)
        if not math.isfinite(period) or period < 0.1:
            raise ValueError('period must be finite and at least 0.1 seconds')
        self.publisher = self.create_publisher(SystemStatus, 'system_status', 1)
        self.collector = Collector()
        self.timer = self.create_timer(period, self.publish_status)

    def publish_status(self):
        try:
            sample = self.collector.sample()
            msg = SystemStatus()
            msg.stamp.sec, msg.stamp.nanosec = divmod(sample.stamp_ns, 1_000_000_000)
            for field in ('hostname', 'cpu_percent', 'memory_percent',
                          'memory_total', 'memory_available', 'net_sent', 'net_recv'):
                setattr(msg, field, getattr(sample, field))
            self.publisher.publish(msg)
        except (OSError, RuntimeError) as exc:
            self.get_logger().error(f'Sampling failed: {exc}')


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SysStatusPub()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
