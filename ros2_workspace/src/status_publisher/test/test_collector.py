"""Deterministic collector check for colcon/pytest."""
from types import SimpleNamespace
from status_publisher.collector import Collector


def test_collector_byte_counts():
    backend = SimpleNamespace(
        cpu_percent=lambda interval: 25.0,
        virtual_memory=lambda: SimpleNamespace(total=1000, available=750, percent=25.0),
        net_io_counters=lambda: SimpleNamespace(bytes_sent=123, bytes_recv=456),
    )
    sample = Collector(backend, clock=lambda: 1_000_000_001).sample()
    assert sample.memory_available == 750
    assert sample.net_recv == 456
    assert sample.stamp_ns == 1_000_000_001
