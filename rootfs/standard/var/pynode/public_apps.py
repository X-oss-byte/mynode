#!/usr/local/bin/python3
import os
import time
import subprocess
import json
from utilities import *


RATHOLE_CONFIG_FILE = "/opt/mynode/rathole/client.toml"

#############################
# PUBLIC API
#############################
def enable_public_apps(public_app_config):
    if public_app_config and len(public_app_config) > 0:
        current_config = get_current_rathole_config()
        new_config = generate_rathole_config(public_app_config)
        if current_config != new_config:
            write_rathole_config(new_config)
    else:
        disable_public_apps()

def disable_public_apps():
    delete_rathole_config()

#############################
# INTERNAL
#############################
def delete_rathole_config():
    # On restart the placeholder config will be generated so the service doesn't fail
    delete_file(RATHOLE_CONFIG_FILE)
    restart_rathole()

def write_rathole_config(config):
    set_file_contents(RATHOLE_CONFIG_FILE, config)

def get_current_rathole_config():
    return get_file_contents(RATHOLE_CONFIG_FILE)

def generate_rathole_config(public_app_config):
    config = "# client.toml\n" + "[client]\n"
    config += "remote_addr = \"mynodebtc.com:2333\"\n"
    config += "retry_interval = 120\n"
    config += "\n"
    for app in public_app_config:
        if "id" in app and "subdomain" in app and "app_name" in app and "rathole_token" in app:
            local_port = get_port_for_app(app["app_name"])
            if local_port != "":
                config += "[client.services." + str(app["id"]) + "_" + app["subdomain"] + "_" + app["app_name"] + "]\n"
                config += "local_addr = \"127.0.0.1:" + local_port + "\"\n"
                config += "token = \"" + app["rathole_token"] + "\"\n"
                config += "\n"
            else:
                config += "# ERROR PROCESSING AN APP (MISSING PORT FOR "+app["app_name"]+")\n\n"
        else:
            config += "# ERROR PROCESSING AN APP (MISSING NAME OR TOKEN)\n\n"
    return config

def restart_rathole():
    os.system("systemctl restart rathole")

def get_port_for_app(app_name):
    # Returns port for app - must be the port being served with the public app tls cert
    app_ports = {"lnbits": "6001", "btcpayserver": "6002", "lndhub": "6003"}
    return app_ports.get(app_name, "")

