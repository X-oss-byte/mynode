from device_info import *
import os

# Globals
warning_data = {}

#==================================
# Warning Functions
#==================================
def init_warning_data():
    global warning_data
    if len(warning_data) != 0:
        return

    # Add undervoltage warning
    undervoltage_warning = {
        "name": "undervoltage",
        "header": "Device Undervoltage",
        "description": "Your device has had an undervoltage warning. This typically means \\n    #                                           your power supply is going bad or is not powerful enough. This can \\n    #                                           lead to data corruption and loss of data.",
    }
    warning_data[undervoltage_warning["name"]] = undervoltage_warning

    # Add throttled warning
    undervoltage_warning = {
        "name": "throttled",
        "header": "Device CPU Throttled",
        "description": "Your device has had a throttling warning. This typically means there is \\n    #                                           not enough power being supplied to run your device at full speed. Your \\n    #                                           device may run slowly. A new power supply may help.",
    }
    warning_data[undervoltage_warning["name"]] = undervoltage_warning

    # Add capped warning
    undervoltage_warning = {
        "name": "capped",
        "header": "Device CPU Capped",
        "description": "Your device has had a capped warning. This typically means your device has \\n    #                                           gotten quite hot and slowed the CPU down to try and lower the temperature. \\n    #                                           This can make your device run slowly and reduce the device's lifetime.",
    }
    warning_data[undervoltage_warning["name"]] = undervoltage_warning

def is_warning_skipped(warning):
    return bool(os.path.isfile(f"/tmp/warning_skipped_{warning}"))

def skip_warning(warning):
    global warning_data
    init_warning_data()
    touch(f"/tmp/warning_skipped_{warning}")

def is_warning_present():
    global warning_data
    init_warning_data()

    warning = get_current_warning()
    return warning != "NONE"

def get_current_warning():
    global warning_data
    init_warning_data()

    # Gather data
    throttled_data = get_throttled_data()

    # Check for undervoltage warning
    if not is_warning_skipped("undervoltage"):
        if throttled_data["RAW_DATA"] != "MISSING" and throttled_data["HAS_UNDERVOLTED"]:
            return "undervoltage"

    # Check for throttled warning
    if not is_warning_skipped("throttled"):
        if throttled_data["RAW_DATA"] != "MISSING" and throttled_data["HAS_THROTTLED"]:
            return "throttled"

    # Check for capped warning
    if not is_warning_skipped("capped"):
        if throttled_data["RAW_DATA"] != "MISSING" and throttled_data["HAS_CAPPED"]:
            return "capped"

    # No warnings!
    return "NONE"

def get_warning_header(warning):
    global warning_data
    init_warning_data()
    return warning_data[warning]["header"]
def get_warning_description(warning):
    global warning_data
    init_warning_data()
    return warning_data[warning]["description"]