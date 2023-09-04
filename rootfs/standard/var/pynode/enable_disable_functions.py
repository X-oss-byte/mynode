import os
import subprocess
from werkzeug.routing import RequestRedirect
from config import *
from systemctl_info import *

# Generic Enable / Disable Function
def enable_service(short_name):
    os.system(f"systemctl enable {short_name} --no-pager")
    os.system(f"systemctl start {short_name} --no-pager")
    open(f"/mnt/hdd/mynode/settings/{short_name}_enabled", 'a').close()
    clear_service_enabled_cache()
    enable_actions(short_name)

def disable_service(short_name):
    enabled_file = f"/mnt/hdd/mynode/settings/{short_name}_enabled"
    if os.path.isfile(enabled_file):
        os.remove(enabled_file)
    disable_actions(short_name)
    os.system(f"systemctl stop {short_name} --no-pager")
    os.system(f"systemctl disable {short_name} --no-pager")
    clear_service_enabled_cache()

# Functions to handle special enable/disable cases
def enable_actions(short_name):
    pass

def disable_actions(short_name):
    if short_name == "electrs":
        # Hard kill since we are disabling
        os.system("killall -9 electrs")
    if short_name == "vpn":
        # Disable OpenVPN as well
        os.system("systemctl stop openvpn --no-pager")
        os.system("systemctl disable openvpn --no-pager")

# Function to start/stop/restart service
def start_service(short_name):
    os.system(f"systemctl start {short_name} --no-pager")
def stop_service(short_name):
    os.system(f"systemctl stop {short_name} --no-pager")
def restart_service(short_name):
    os.system(f"systemctl restart {short_name} --no-pager")

