import json

from flask import Flask

from titus_isolate.isolate.detect import get_cross_package_violations, get_shared_core_violations

app = Flask(__name__)
__workload_manager = None
__event_manager = None


def set_wm(workload_manager):
    global __workload_manager
    __workload_manager = workload_manager


def set_em(event_manager):
    global __event_manager
    __event_manager = event_manager


@app.route('/workloads')
def get_workloads():
    workloads = [w.to_dict() for w in __workload_manager.get_workloads()]
    return json.dumps(workloads)


@app.route('/cpu')
def get_cpu():
    packages = []
    for p in __workload_manager.get_cpu().get_packages():

        cores = []
        for c in p.get_cores():

            threads = []
            for t in c.get_threads():
                threads.append({
                    "id": t.get_id(),
                    "workload_id": t.get_workload_id()
                })
            cores.append({
                "id": c.get_id(),
                "threads": threads
            })

        packages.append({
            "id": p.get_id(),
            "cores": cores
        })

    response = {
        "packages": packages
    }

    return json.dumps(response)


@app.route('/violations')
def get_violations():
    return json.dumps({
        "cross_package": get_cross_package_violations(__workload_manager.get_cpu()),
        "shared_core": get_shared_core_violations(__workload_manager.get_cpu())
    })


@app.route('/status')
def get_wm_status():
    return json.dumps({
        "event_manager": {
            "queue_depth": __event_manager.get_queue_depth(),
            "success_count": __event_manager.get_success_count(),
            "error_count": __event_manager.get_error_count(),
            "processed_count": __event_manager.get_processed_count()
        },
        "workload_manager": {
            "cpu_allocator": __workload_manager.get_allocator_name(),
            "workload_count": len(__workload_manager.get_workloads()),
            "success_count": __workload_manager.get_success_count(),
            "error_count": __workload_manager.get_error_count(),
            "added_count": __workload_manager.get_added_count(),
            "removed_count": __workload_manager.get_removed_count()
        }
    })
