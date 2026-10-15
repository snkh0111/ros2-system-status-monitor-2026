"""Host sampling independent of ROS; memory and network are byte counts."""
from dataclasses import dataclass
import platform
import time


@dataclass(frozen=True)
class Sample:
    stamp_ns: int
    hostname: str
    cpu_percent: float
    memory_percent: float
    memory_total: int
    memory_available: int
    net_sent: int
    net_recv: int


class Collector:
    """Prime nonblocking CPU measurement once, then collect between timer ticks."""

    def __init__(self, backend=None, clock=time.time_ns):
        if backend is None:
            import psutil
            backend = psutil
        self.backend = backend
        self.clock = clock
        self.hostname = platform.node()
        self.backend.cpu_percent(interval=None)

    def sample(self):
        memory = self.backend.virtual_memory()
        network = self.backend.net_io_counters()
        if network is None:
            raise RuntimeError('Network counters unavailable')
        cpu = float(self.backend.cpu_percent(interval=None))
        return Sample(self.clock(), self.hostname, cpu, float(memory.percent),
                      int(memory.total), int(memory.available),
                      int(network.bytes_sent), int(network.bytes_recv))


def rates(previous, current):
    """Return B/s or None on initial sample, clock reversal or counter reset."""
    if previous is None or current.hostname != previous.hostname:
        return None
    elapsed = (current.stamp_ns - previous.stamp_ns) / 1e9
    sent = current.net_sent - previous.net_sent
    recv = current.net_recv - previous.net_recv
    if elapsed <= 0 or sent < 0 or recv < 0:
        return None
    return sent / elapsed, recv / elapsed
