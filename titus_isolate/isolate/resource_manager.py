import logging

from titus_isolate.docker.constants import STATIC, BURST
from titus_isolate.isolate.cpu import assign_threads, free_threads

log = logging.getLogger()


class ResourceManager:

    def __init__(self, cpu, docker_client):
        self.__cpu = cpu
        self.__docker_client = docker_client

    def assign_threads(self, workload):
        threads = []
        if workload.get_type() == STATIC:
            threads = assign_threads(self.__cpu, workload)
        elif workload.get_type() == BURST:
            threads = self.__cpu.get_empty_threads()

        thread_ids = self.__get_thread_ids_str(threads)
        log.info("Updating container: '{}' with cpuset_cpus: '{}'".format(workload.get_id(), thread_ids))
        self.__docker_client.containers.get(workload.get_id()).update(cpuset_cpus=thread_ids)
        return threads

    def free_threads(self, workload_id):
        return free_threads(self.__cpu, workload_id)

    @staticmethod
    def __get_thread_ids_str(threads):
        thread_ids = [str(thread.get_id()) for thread in threads]
        return ",".join(thread_ids)