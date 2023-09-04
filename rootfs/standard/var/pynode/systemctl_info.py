import os
import subprocess
from utilities import *

service_enabled_cache = {}

#==================================
# Service Status, Enabled, Logs, etc...
#==================================
def clear_service_enabled_cache():
    global service_enabled_cache
    service_enabled_cache = {}

def is_service_enabled(service_name, force_refresh=False):
    global service_enabled_cache

    if service_name in service_enabled_cache and force_refresh == False:
        return service_enabled_cache[service_name]

    code = os.system(f"systemctl is-enabled {service_name} > /dev/null 2>&1")
    if code == 0:
        service_enabled_cache[service_name] = True
        return True
    service_enabled_cache[service_name] = False
    return False

def get_service_status_code(service_name):
    return os.system(
        f"systemctl status {service_name} --no-pager > /dev/null 2>&1"
    )

def get_service_status_basic_text(service_name):
    if not is_service_enabled(service_name):
        return "Disabled"

    code = os.system(
        f"systemctl status {service_name} --no-pager  > /dev/null 2>&1"
    )
    return "Running" if code == 0 else "Error"

def get_service_status_color(service_name):
    if not is_service_enabled(service_name):
        return "gray"

    code = os.system(
        f"systemctl status {service_name} --no-pager > /dev/null 2>&1"
    )
    return "green" if code == 0 else "red"

def get_journalctl_log(service_name):
    try:
        log = to_string(
            subprocess.check_output(
                f"journalctl -r --unit={service_name} --no-pager | head -n 300",
                shell=True,
            ).decode("utf8")
        )
    except:
        log = "ERROR"
    return log
