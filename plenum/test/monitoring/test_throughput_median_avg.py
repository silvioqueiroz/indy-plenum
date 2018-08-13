import functools

import pytest

from plenum.server.instances import Instances
from plenum.server.monitor import ThroughputMeasurement, Monitor
from plenum.test.testing_utils import FakeSomething

NUM_OF_REPLICAS = 5


@pytest.fixture(scope='function')
def fake_monitor(tconf):
    def getThroughput(self, instId):
        return self.throughputs[instId].throughput

    throughputs = []
    instances = Instances()
    for i in range(NUM_OF_REPLICAS):
        throughputs.append(ThroughputMeasurement(first_ts=0))
        instances.add()
    monitor = FakeSomething(
        throughputs=throughputs,
        instances=instances,
        Delta=tconf.DELTA,
        )
    monitor.numOrderedRequests = []
    for i in range(NUM_OF_REPLICAS):
        monitor.numOrderedRequests.append((100, 100))
    monitor.getThroughputs = functools.partial(Monitor.getThroughputs, monitor)
    monitor.getThroughput = functools.partial(getThroughput, monitor)
    monitor.getInstanceMetrics = functools.partial(Monitor.getInstanceMetrics, monitor)
    monitor.masterThroughputRatio = functools.partial(Monitor.masterThroughputRatio, monitor)
    return monitor


def test_low_median(fake_monitor, tconf):
    monitor = fake_monitor
    # Filling for case, when the most of backup throughputs are small and several is very big
    # Case is [100, 120, 120, 120, 10000]
    monitor.throughputs[0].throughput = 100
    monitor.throughputs[-1].throughput = 10000
    for i in range(1, NUM_OF_REPLICAS - 1):
        monitor.throughputs[i].throughput = 120
    assert monitor.masterThroughputRatio() > tconf.DELTA


def test_medium_median(fake_monitor, tconf):
    monitor = fake_monitor
    # Filling for case, when the most of backup throughputs a similar with master,
    # but there is a very small and a very big
    # Case is [100, 1, 120, 120, 10000]
    monitor.throughputs[0].throughput = 100
    monitor.throughputs[1].throughput = 1
    monitor.throughputs[-1].throughput = 10000
    for i in range(2, NUM_OF_REPLICAS - 1):
        monitor.throughputs[i].throughput = 120
    assert monitor.masterThroughputRatio() > tconf.DELTA


def test_high_median(fake_monitor, tconf):
    monitor = fake_monitor
    # Filling for case, when the most os backup throughputs a similar with master,
    # but there is a some very big values
    # Case is [100, 1000, 120, 120, 10000]
    monitor.throughputs[0].throughput = 100
    monitor.throughputs[1].throughput = 1000
    monitor.throughputs[-1].throughput = 10000
    for i in range(2, NUM_OF_REPLICAS - 1):
        monitor.throughputs[i].throughput = 120
    assert monitor.masterThroughputRatio() > tconf.DELTA
