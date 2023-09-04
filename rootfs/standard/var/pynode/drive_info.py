from config import *
from utilities import *
import time
import json
import os
import subprocess
import random
import string
import re


#==================================
# Drive Functions
#==================================
def is_mynode_drive_mounted():
    mounted = True
    try:
        # Command fails and throws exception if not mounted
        output = to_string(subprocess.check_output("grep -qs '/mnt/hdd ' /proc/mounts", shell=True))
    except:
        mounted = False
    return mounted

def is_device_mounted(d):
    mounted = True
    try:
        # Command fails and throws exception if not mounted
        ls_output = to_string(
            subprocess.check_output(
                f"grep -qs '/dev/{d}' /proc/mounts", shell=True
            )
        )
    except:
        mounted = False
    return mounted

def get_drive_size(drive):
    size = -1
    try:
        lsblk_output = to_string(
            subprocess.check_output(
                f"lsblk -b /dev/{drive} | grep disk", shell=True
            )
        )
        parts = lsblk_output.split()
        size = int(parts[3])
    except:
        pass
    #log_message(f"Drive {drive} size: {size}")
    return size

def get_mynode_drive_size():
    size = -1
    if not is_mynode_drive_mounted():
        return -3
    try:
        size = to_string(subprocess.check_output("df /mnt/hdd | grep /dev | awk '{print $2}'", shell=True)).strip()
        size = int(size) / 1000 / 1000
    except Exception as e:
        size = -2
    return size

def get_data_drive_usage():
    if is_cached("data_drive_usage", 300):
        return get_cached_data("data_drive_usage")
    usage = "0%"
    try:
        if not is_mynode_drive_mounted():
            return "N/A"
        usage = to_string(subprocess.check_output("df -h /mnt/hdd | grep /dev | awk '{print $5}'", shell=True))
        update_cached_data("data_drive_usage", usage)
    except:
        return usage
    return usage
        
def get_os_drive_usage():
    if is_cached("os_drive_usage", 300):
        return get_cached_data("os_drive_usage")
    usage = "0%"
    try:
        usage = to_string(subprocess.check_output("df -h / | grep /dev | awk '{print $5}'", shell=True))
        update_cached_data("os_drive_usage", usage)
    except:
        return usage
    return usage

def check_partition_for_mynode(partition):
    is_mynode = False
    try:
        subprocess.check_output(f"mount -o ro /dev/{partition} /mnt/hdd", shell=True)
        if os.path.isfile("/mnt/hdd/.mynode"):
            is_mynode = True
    except Exception as e:
        # Mount failed, could be target drive
        pass
    finally:
        time.sleep(1)
        os.system("umount /mnt/hdd")

    return is_mynode

def find_partitions_for_drive(drive):
    partitions = []
    try:
        ls_output = to_string(
            subprocess.check_output(
                f"ls /sys/block/{drive}/ | grep {drive}", shell=True
            )
        )
        partitions = ls_output.split()
    except:
        pass
    return partitions

def is_device_detected_by_fdisk(d):
    detected = False
    try:
        # Command fails and throws exception if not mounted
        output = to_string(subprocess.check_output(f"fdisk -l /dev/{d}", shell=True))
        detected = True
    except:
        pass
    return detected

def find_unmounted_drives():
    drives = []
    try:
        ls_output = subprocess.check_output("ls /sys/block/ | egrep 'hd.*|vd.*|sd.*|nvme.*'", shell=True).decode("utf-8")
        all_drives = ls_output.split()

        # Only return drives that are not mounted (VM may have /dev/sda as OS drive)
        drives.extend(
            d
            for d in all_drives
            if is_device_detected_by_fdisk(d) and not is_device_mounted(d)
        )
    except:
        pass
    return drives

#==================================
# Drive Format Functions
#==================================
def set_drive_filesystem_type(filesystem):
    run_linux_cmd("rm -f /tmp/format_filesystem_*")
    touch(f"/tmp/format_filesystem_{filesystem}")
    run_linux_cmd("sync")

def get_current_drive_filesystem_type():
    if not is_mynode_drive_mounted():
        return "not_mounted"
    try:
        with open("/proc/mounts") as f:
            lines = f.readlines()
            for line in lines:
                parts = line.split(" ")
                if len(parts) >= 3 and parts[1] == "/mnt/hdd":
                    return parts[2]
    except Exception as e:
        log_message(f"ERROR: Cannot determine drive filesystem type ({str(e)})")
    return "error"

#==================================
# Mount / Unmount Parition Functions
#==================================
def mount_partition(partition, folder_name, permissions="ro"):
    try:
        subprocess.check_output(f"mkdir -p /mnt/usb_extras/{folder_name}", shell=True)
        subprocess.check_output(
            f"mount -o {permissions} /dev/{partition} /mnt/usb_extras/{folder_name}",
            shell=True,
        )
        return True
    except Exception as e:
        return False

def unmount_partition(folder_name):
    os.system(f"umount /mnt/usb_extras/{folder_name}")
    os.system(f"rm -rf /mnt/usb_extras/{folder_name}")
    time.sleep(1)


#==================================
# Drive Driver Functions
#==================================
def is_uas_usb_enabled():
    return settings_file_exists("uas_usb_enabled")
