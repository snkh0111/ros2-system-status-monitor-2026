"""Record actual host samples; not a ROS2 transport or Ubuntu test."""
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ros2_workspace/src/status_publisher'))
from status_publisher.collector import Collector, rates
import psutil

collector = Collector()
previous = None
records = []
for _ in range(3):
    time.sleep(1)
    current = collector.sample()
    assert 0 <= current.cpu_percent <= 100
    assert 0 <= current.memory_percent <= 100
    assert 0 <= current.memory_available <= current.memory_total
    assert current.net_sent >= 0 and current.net_recv >= 0
    records.append({'sample': asdict(current), 'rates_B_per_s': rates(previous, current)})
    previous = current
result = {
    'recorded_at': datetime.now().astimezone().isoformat(),
    'platform': platform.platform(), 'python': sys.version,
    'psutil': psutil.__version__, 'scope': 'Real Windows host collection, no ROS2/Qt',
    'records': records,
}
target = ROOT / 'evidence/host_samples.json'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: 3 real host samples; range checks passed. Not a ROS2 test.')
print('Evidence:', target)
