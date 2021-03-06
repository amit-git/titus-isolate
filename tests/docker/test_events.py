import logging
import unittest
import uuid

from tests.config.test_property_provider import TestPropertyProvider
from tests.docker.mock_docker import get_container_create_event, MockDockerClient, MockEventProvider, get_event, \
    get_container_die_event, MockContainer
from tests.utils import config_logs, wait_until, TestContext, get_mock_file_manager
from titus_isolate.config.config_manager import ConfigManager
from titus_isolate.docker.constants import CONTAINER, CREATE, STATIC, CPU_LABEL_KEY, WORKLOAD_TYPE_LABEL_KEY, NAME
from titus_isolate.docker.event_manager import EventManager
from titus_isolate.model.processor.utils import DEFAULT_TOTAL_THREAD_COUNT
from titus_isolate.model.workload import Workload
from titus_isolate.utils import override_config_manager

DEFAULT_CPU_COUNT = 2

config_logs(logging.DEBUG)

DEFAULT_TEST_EVENT_TIMEOUT_SECS = 0.01
override_config_manager(ConfigManager(TestPropertyProvider({})))


class TestEvents(unittest.TestCase):

    def test_update_mock_container(self):
        workload_name = str(uuid.uuid4())
        workload = Workload(workload_name, DEFAULT_CPU_COUNT, STATIC)
        docker_client = MockDockerClient([MockContainer(workload)])

        events = [get_container_create_event(DEFAULT_CPU_COUNT, STATIC, workload_name, workload_name)]
        event_count = len(events)
        event_iterable = MockEventProvider(events)

        test_context = TestContext(docker_client)
        manager = EventManager(event_iterable, test_context.get_event_handlers(), get_mock_file_manager(), DEFAULT_TEST_EVENT_TIMEOUT_SECS)

        wait_until(lambda: event_count == manager.get_processed_count())
        self.assertEqual(0, manager.get_queue_depth())
        self.assertEqual(event_count, test_context.get_workload_manager().get_success_count())
        self.assertEqual(DEFAULT_TOTAL_THREAD_COUNT - DEFAULT_CPU_COUNT, len(test_context.get_cpu().get_empty_threads()))
        self.assertEqual(1, test_context.get_create_event_handler().get_handled_event_count())

        manager.stop_processing_events()

    def test_free_cpu_on_container_die(self):
        workload_name = str(uuid.uuid4())
        workload = Workload(workload_name, DEFAULT_CPU_COUNT, STATIC)
        docker_client = MockDockerClient([MockContainer(workload)])

        events = [
            get_container_create_event(DEFAULT_CPU_COUNT, STATIC, workload_name, workload_name),
            get_container_die_event(workload_name)]
        event_count = len(events)
        event_iterable = MockEventProvider(events, 1)  # Force in order event processing for the test

        test_context = TestContext(docker_client)
        manager = EventManager(event_iterable, test_context.get_event_handlers(), get_mock_file_manager(), DEFAULT_TEST_EVENT_TIMEOUT_SECS)

        wait_until(lambda: event_count == manager.get_processed_count())
        self.assertEqual(0, manager.get_queue_depth())
        self.assertEqual(DEFAULT_TOTAL_THREAD_COUNT, len(test_context.get_cpu().get_empty_threads()))
        self.assertEqual(1, test_context.get_create_event_handler().get_handled_event_count())
        self.assertEqual(1, test_context.get_free_event_handler().get_handled_event_count())

        manager.stop_processing_events()

    def test_unknown_action(self):
        test_context = TestContext()
        unknown_event = get_event(CONTAINER, "unknown", uuid.uuid4(), {})
        event_iterable = MockEventProvider([unknown_event])
        manager = EventManager(event_iterable, test_context.get_event_handlers(), get_mock_file_manager(), DEFAULT_TEST_EVENT_TIMEOUT_SECS)

        wait_until(lambda: test_context.get_create_event_handler().get_ignored_event_count() == 1)
        self.assertEqual(0, manager.get_queue_depth())

        manager.stop_processing_events()

    def test_absent_cpu_label(self):
        test_context = TestContext()
        unknown_event = get_event(
            CONTAINER,
            CREATE,
            "unknown",
            {
                WORKLOAD_TYPE_LABEL_KEY: STATIC,
                NAME: str(uuid.uuid4())
            })
        event_iterable = MockEventProvider([unknown_event])
        manager = EventManager(event_iterable, test_context.get_event_handlers(), get_mock_file_manager(), DEFAULT_TEST_EVENT_TIMEOUT_SECS)

        wait_until(lambda: test_context.get_create_event_handler().get_ignored_event_count() == 1)
        self.assertEqual(0, manager.get_queue_depth())

        manager.stop_processing_events()

    def test_absent_workload_type_label(self):
        test_context = TestContext()
        name = str(uuid.uuid4())
        unknown_event = get_event(
            CONTAINER,
            CREATE,
            name,
            {
                CPU_LABEL_KEY: "1",
                NAME: name
            })
        event_handlers = test_context.get_event_handlers()
        event_iterable = MockEventProvider([unknown_event])
        manager = EventManager(event_iterable, event_handlers, get_mock_file_manager(), DEFAULT_TEST_EVENT_TIMEOUT_SECS)

        wait_until(lambda: test_context.get_create_event_handler().get_ignored_event_count() == 1)
        self.assertEqual(0, manager.get_queue_depth())

        manager.stop_processing_events()

    def test_unknown_workload_type_label(self):
        test_context = TestContext()
        unknown_event = get_event(
            CONTAINER,
            CREATE,
            uuid.uuid4(),
            {NAME: "container-name", CPU_LABEL_KEY: "1", WORKLOAD_TYPE_LABEL_KEY: "unknown"})
        valid_event = get_container_create_event(1)
        event_iterable = MockEventProvider([unknown_event, valid_event])
        manager = EventManager(event_iterable, test_context.get_event_handlers(), get_mock_file_manager(), DEFAULT_TEST_EVENT_TIMEOUT_SECS)

        wait_until(lambda: manager.get_error_count() == 1)
        wait_until(lambda: manager.get_processed_count() == 2)
        self.assertEqual(0, manager.get_queue_depth())

        manager.stop_processing_events()

