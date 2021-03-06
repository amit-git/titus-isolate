from titus_isolate import log
from titus_isolate.isolate.detect import get_cross_package_violations, get_shared_core_violations
from titus_isolate.metrics.metrics_reporter import MetricsReporter

ADDED_KEY = 'titus-isolate.added'
REMOVED_KEY = 'titus-isolate.removed'
SUCCEEDED_KEY = 'titus-isolate.succeeded'
FAILED_KEY = 'titus-isolate.failed'
ALLOCATOR_CALL_DURATION = 'titus-isolate.allocatorCallDurationSecs'
FALLBACK_ALLOCATOR_COUNT = 'titus-isolate.fallbackCount'
IP_ALLOCATOR_TIMEBOUND_COUNT = 'titus-isolate.ipAllocatorTimeBoundSolutionCount'
QUEUE_DEPTH_KEY = 'titus-isolate.queueDepth'
WORKLOAD_COUNT_KEY = 'titus-isolate.workloadCount'
EVENT_SUCCEEDED_KEY = 'titus-isolate.eventSucceeded'
EVENT_FAILED_KEY = 'titus-isolate.eventFailed'
EVENT_PROCESSED_KEY = 'titus-isolate.eventProcessed'

PACKAGE_VIOLATIONS_KEY = 'titus-isolate.crossPackageViolations'
CORE_VIOLATIONS_KEY = 'titus-isolate.sharedCoreViolations'

RUNNING = 'titus-isolate.running'


class InternalMetricsReporter(MetricsReporter):

    def __init__(self, workload_manager, event_manager):
        self.__workload_manager = workload_manager
        self.__event_manager = event_manager
        self.__reg = None

    def set_registry(self, registry):
        self.__reg = registry

    def report_metrics(self, tags):
        log.debug("Reporting metrics")
        try:
            # Workload manager metrics
            self.__reg.gauge(RUNNING, tags).set(1)

            self.__reg.gauge(ADDED_KEY, tags).set(self.__workload_manager.get_added_count())
            self.__reg.gauge(REMOVED_KEY, tags).set(self.__workload_manager.get_removed_count())
            self.__reg.gauge(SUCCEEDED_KEY, tags).set(self.__workload_manager.get_success_count())
            self.__reg.gauge(FAILED_KEY, tags).set(self.__workload_manager.get_error_count())
            self.__reg.gauge(WORKLOAD_COUNT_KEY, tags).set(len(self.__workload_manager.get_workloads()))

            # Allocator metrics
            self.__reg.gauge(ALLOCATOR_CALL_DURATION, tags).set(self.__workload_manager.get_allocator_call_duration_sum_secs())
            self.__reg.gauge(FALLBACK_ALLOCATOR_COUNT, tags).set(self.__workload_manager.get_fallback_allocator_calls_count())
            self.__reg.gauge(IP_ALLOCATOR_TIMEBOUND_COUNT, tags).set(self.__workload_manager.get_time_bound_ip_allocator_solution_count())

            # Event manager metrics
            self.__reg.gauge(QUEUE_DEPTH_KEY, tags).set(self.__event_manager.get_queue_depth())
            self.__reg.gauge(EVENT_SUCCEEDED_KEY, tags).set(self.__event_manager.get_success_count())
            self.__reg.gauge(EVENT_FAILED_KEY, tags).set(self.__event_manager.get_error_count())
            self.__reg.gauge(EVENT_PROCESSED_KEY, tags).set(self.__event_manager.get_processed_count())

            # CPU metrics
            cross_package_violation_count = len(get_cross_package_violations(self.__workload_manager.get_cpu()))
            shared_core_violation_count = len(get_shared_core_violations(self.__workload_manager.get_cpu()))
            self.__reg.gauge(PACKAGE_VIOLATIONS_KEY, tags).set(cross_package_violation_count)
            self.__reg.gauge(CORE_VIOLATIONS_KEY, tags).set(shared_core_violation_count)
            log.debug("Reported metrics")

        except:
            log.exception("Failed to report metric")
