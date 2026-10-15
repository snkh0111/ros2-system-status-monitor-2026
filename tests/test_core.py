"""Offline tests; these do not exercise ROS2 or Qt."""
import ast
from dataclasses import replace
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ros2_workspace/src/status_publisher'))
from status_publisher.collector import Collector, Sample, rates


class Backend:
    def __init__(self):
        self.cpu_calls = 0

    def cpu_percent(self, interval):
        assert interval is None
        self.cpu_calls += 1
        return 12.5

    def virtual_memory(self):
        return SimpleNamespace(total=2**36, available=2**35, percent=50.0)

    def net_io_counters(self):
        return SimpleNamespace(bytes_sent=2**48, bytes_recv=2**49)


class CoreTests(unittest.TestCase):
    def test_sampling_units_precision_and_cpu_priming(self):
        backend = Backend()
        result = Collector(backend, lambda: 1234567890).sample()
        self.assertEqual(backend.cpu_calls, 2)
        self.assertEqual(result.stamp_ns, 1234567890)
        self.assertEqual(result.memory_total, 2**36)
        self.assertEqual(result.net_sent, 2**48)
        self.assertEqual(result.cpu_percent, 12.5)

    def test_network_unavailable_is_error(self):
        backend = Backend()
        backend.net_io_counters = lambda: None
        with self.assertRaises(RuntimeError):
            Collector(backend).sample()

    def test_rates_and_invalid_intervals(self):
        first = Sample(1_000_000_000, 'host', 0., 0., 1, 1, 100, 200)
        later = replace(first, stamp_ns=3_000_000_000, net_sent=300, net_recv=800)
        self.assertEqual(rates(first, later), (100., 300.))
        self.assertIsNone(rates(None, later))
        self.assertIsNone(rates(first, first))
        self.assertIsNone(rates(later, first))
        self.assertIsNone(rates(first, replace(later, net_sent=0)))
        self.assertIsNone(rates(first, replace(later, hostname='other')))

    def test_interface_schema_and_package_manifests(self):
        source = ROOT / 'ros2_workspace/src'
        fields = [line.split() for line in
                  (source / 'status_interfaces/msg/SystemStatus.msg').read_text().splitlines()
                  if line.strip() and not line.startswith('#')]
        self.assertEqual(fields, [
            ['builtin_interfaces/Time', 'stamp'], ['string', 'hostname'],
            ['float32', 'cpu_percent'], ['float32', 'memory_percent'],
            ['uint64', 'memory_total'], ['uint64', 'memory_available'],
            ['uint64', 'net_sent'], ['uint64', 'net_recv']])
        for name, build_type in [('status_interfaces', 'ament_cmake'),
                                 ('status_publisher', 'ament_python')]:
            tree = ET.parse(source / name / 'package.xml')
            self.assertEqual(tree.findtext('name'), name)
            self.assertEqual(tree.findtext('export/build_type'), build_type)
        self.assertTrue((source / 'status_publisher/resource/status_publisher').is_file())

    def test_python_syntax(self):
        for file in (ROOT / 'ros2_workspace').rglob('*.py'):
            ast.parse(file.read_text(encoding='utf-8'), filename=str(file))


if __name__ == '__main__':
    unittest.main(verbosity=2)
