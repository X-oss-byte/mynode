#!/usr/local/bin/python3
import os
import requests
import time
import subprocess
import random
import json
import logging
import argparse
from systemd import journal
from utilities import *
from drive_info import *
from device_info import *

CHECKIN_URL = "https://www.mynodebtc.com/device_api/check_in.php"

log = logging.getLogger('check_in')
log.addHandler(journal.JournaldLogHandler())
log.setLevel(logging.INFO)
set_logger(log)

latest_version_check_count = 0

# Helper functions
def clear_response_data():
    os.system("rm -f /tmp/check_in_response.json")
def save_response_data(data):
    try:
        with open("/tmp/check_in_response.json", "w") as file:
            json.dump(data, file, indent=4, sort_keys=True)
    except Exception as e:
        log_message(
            f"save_response_data exception: failed to save response - {str(e)}"
        )

def get_quicksync_enabled():
    if not is_mynode_drive_mounted():
        return -3
    return (
        0
        if os.path.isfile("/mnt/hdd/mynode/settings/quicksync_disabled")
        else 1
    )

def check_for_new_mynode_version():
    global latest_version_check_count
    # Chances of refreshing version
    #   Note: Hard limit forces day 5 to 100%
    # 
    # A 30% chance per day is:  A 35% chance per day is:  A 40% chance per day is:  A 45% chance per day is:
    #  1 day(s): 30%             1 day(s): 35%             1 day(s): 40%             1 day(s): 45%
    #  2 day(s): 51%             2 day(s): 57%             2 day(s): 64%             2 day(s): 69%
    #  3 day(s): 65%             3 day(s): 72%             3 day(s): 78%             3 day(s): 83%
    #  5 day(s): 83%             5 day(s): 88%             5 day(s): 92%             5 day(s): 94%
    #  7 day(s): 91%             7 day(s): 95%             7 day(s): 97%             7 day(s): 98%
    # A 50% chance per day is:  A 55% chance per day is:  A 60% chance per day is:  A 65% chance per day is:
    #  1 day(s): 50%             1 day(s): 55%             1 day(s): 60%             1 day(s): 65%
    #  2 day(s): 75%             2 day(s): 79%             2 day(s): 84%             2 day(s): 87%
    #  3 day(s): 87%             3 day(s): 90%             3 day(s): 93%             3 day(s): 95%
    #  5 day(s): 96%             5 day(s): 98%             5 day(s): 99%             5 day(s): 99%
    #  7 day(s): 99.2%           7 day(s): 99.6%           7 day(s): 99.8%           7 day(s): 99.9%
    if latest_version_check_count % 5 == 0 or random.randint(1, 100) <= 40:
        log_message(
            f"Version Check Count ({latest_version_check_count}) - Checking for new version!"
        )
        os.system("/usr/bin/mynode_get_latest_version.sh &")
    else:
        log_message(
            f"Version Check Count ({latest_version_check_count}) - Skipping version check"
        )
    latest_version_check_count = latest_version_check_count + 1

def on_check_in_error(msg):
    clear_response_data()
    log_message(msg)
    data = {"status": "ERROR", "message": msg}
    save_response_data(data)

# Checkin every 24 hours
def check_in(check_for_updates):

    # Check for new version (not every time to spread out upgrades)
    if check_for_updates:
        check_for_new_mynode_version()

    # Setup tor proxy
    session = requests.session()
    session.proxies = {
        'http': 'socks5h://localhost:9050',
        'https': 'socks5h://localhost:9050',
    }
    # Check In
    fail_count = 0
    check_in_success = False
    while not check_in_success:
        try:
            repeat_delay = 2*60
            if fail_count <= 5:
                repeat_delay = 2*60
            elif fail_count <= 10:
                repeat_delay = 5*60
            elif fail_count <= 20:
                repeat_delay = 60*60
            else:
                repeat_delay = 6*60*60

            # Gather check in data
            product_key = get_product_key()
            data = {
                "serial": get_device_serial(),
                "device_type": get_device_type(),
                "device_arch": get_device_arch(),
                "debian_version": get_debian_version(),
                "version": get_current_version(),
                "product_key": product_key,
                "drive_size": get_mynode_drive_size(),
                "quicksync_enabled": get_quicksync_enabled(),
                "api_version": 2,
            }

            # Use tor for check in unless there have been several tor failures
            r = None
            if (fail_count+1) % 4 == 0:
                r = requests.post(CHECKIN_URL, data=data, timeout=20)
            else:
                r = session.post(CHECKIN_URL, data=data, timeout=20)

            if r is None:
                on_check_in_error("Check In Failed: (retrying) None")
            elif r.status_code != 200:
                on_check_in_error(f"Check In Failed: (retrying) HTTP ERROR {r.status_code}")
            else:
                try:
                    info = json.loads(r.text)
                    save_response_data(info)

                    try:
                        if info["status"] == "OK":
                            # Check in was successful!
                            if product_key != "community_edition":
                                unset_skipped_product_key()
                            delete_product_key_error()

                            os.system("rm -f /tmp/check_in_error")
                            check_in_success = True
                            log_message(f"Check In Success: {r.text}")
                        else:
                            mark_product_key_error()
                            on_check_in_error(f'Check In Returned Error: {info["status"]} - {r.text}')
                    except Exception as e:
                        on_check_in_error(
                            f"Check In Failed: Error Parsing Response - {str(e)} - {r.text}"
                        )
                except Exception as e:
                    on_check_in_error(f"Check In Failed: Error Parsing JSON - {str(e)}")
        except Exception as e:
            on_check_in_error(f"Check In Failed: (retrying) Exception {e}")
        finally:
            if not check_in_success:
                # Check in failed, try again later
                os.system("touch /tmp/check_in_error")
                time.sleep(repeat_delay)
                fail_count = fail_count + 1

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delay", type=int, default=0,
                        help="Time in seconds to delay before opening connection")
    parser.add_argument("-i", "--interval", type=int, default=0,
                        help="Time in hours to delay before opening connection")
    parser.add_argument("-u", "--check-for-updates", action='store_true',
                        help="Time in hours to delay before opening connection")
    args = parser.parse_args()

    delay = args.delay
    interval = 60*60*args.interval
    while True:
        print(f"Sleeping {delay} seconds...")
        time.sleep(delay)

        check_in(args.check_for_updates)

        if args.interval == 0:
            break
        print(f"Sleeping {interval - delay} seconds...")
        time.sleep(interval - delay)
