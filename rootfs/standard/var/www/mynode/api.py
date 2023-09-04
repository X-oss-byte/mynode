
from flask import Blueprint, render_template, redirect, jsonify, request, send_file
from flask import current_app as app
from user_management import check_logged_in
from bitcoin_info import *
from lightning_info import *
from electrum_info import *
from device_info import *
from thread_functions import *
from systemctl_info import *
from application_info import *
from drive_info import *
from price_info import *
from messages import *
if isPython3():
    from io import StringIO, BytesIO
else:
    import cStringIO
import json
import subprocess
import re
import os

mynode_api = Blueprint('mynode_api',__name__)


### Page functions
@mynode_api.route("/api/ping")
def api_ping():
    check_logged_in()

    data = {"status": get_mynode_status()}
    data["uptime_seconds"] = get_system_uptime_in_seconds()
    return jsonify(data)

@mynode_api.route("/api/get_bitcoin_info")
def api_get_bitcoin_info():
    check_logged_in()

    data = {"current_block": get_mynode_block_height()}
    data["block_height"] = get_bitcoin_block_height()
    data["progress"] = get_bitcoin_sync_progress()
    data["peer_count"] = get_bitcoin_peer_count()
    #data["difficulty"] = get_bitcoin_difficulty() # Dont send difficulty, it causes errors in jsonify
    data["mempool_size"] = get_bitcoin_mempool_info()["display_bytes"]
    data["recommended_fees"] = get_bitcoin_recommended_fees()

    # Add blocks
    data["recent_blocks"] = None
    blocks = get_bitcoin_recent_blocks()
    if blocks != None:
        for b in blocks:
            # Remove TX list for faster processing
            b["tx"] = None
            # Remove difficulty since JSON can't parse large floats (???)
            b["difficulty"] = None
        data["recent_blocks"] = blocks

    #log_message("api_get_bitcoin_info data: "+json.dumps(data))
    return jsonify(data)

@mynode_api.route("/api/get_lightning_info")
def api_get_lightning_info():
    check_logged_in()

    data = {"peer_count": get_lightning_peer_count()}
    data["channel_count"] = get_lightning_channel_count()
    data["lnd_ready"] = is_lnd_ready()
    data["balances"] = get_lightning_balance_info()
    data["channels"] = get_lightning_channels()
    data["transactions"] = get_lightning_transactions()
    data["payments_and_invoices"] = get_lightning_payments_and_invoices()

    return jsonify(data)

@mynode_api.route("/api/get_price_info")
def api_get_price_info():
    check_logged_in()

    data = {"price": get_latest_price()}
    data["delta"] = get_price_diff_24hrs()
    data["direction"] = get_price_up_down_flat_24hrs()

    return jsonify(data)

@mynode_api.route("/api/get_service_status")
def api_get_service_status():
    check_logged_in()

    service = request.args.get('service')

    data = {
        "color": "",
        "sso_token": "",
        "status": get_application_status(service),
    }
    data["status_basic"] = get_service_status_basic_text(service)
    data["color"] = get_application_status_color(service)
    data["sso_token"] = get_application_sso_token(service)
    data["sso_token_enabled"] = get_application_sso_token_enabled(service)
    return jsonify(data)

@mynode_api.route("/api/get_app_info")
def api_get_app_info():
    check_logged_in()

    data = {"status": "ERROR"}
    if request.args.get('app'):
        name = request.args.get('app')
        if is_application_valid(name):
            data = get_application( name )
        else:
            data["status"] = "INVALID APPLICATION"
    else:
        data = get_all_applications()

    return jsonify(data)

@mynode_api.route("/api/restart_app")
def api_restart_app():
    check_logged_in()

    app = request.args.get("app")
    if not app:
        return "NO_APP_SPECIFIED"
    if not is_application_valid(app):
        return "INVALID_APP_NAME"
    return "ERROR" if not restart_application(app) else "OK"

@mynode_api.route("/api/get_device_info")
def api_get_device_info():
    check_logged_in()

    data = {"data_drive_usage": get_data_drive_usage()}
    data["cpu"] = get_cpu_usage()
    data["ram"] = get_ram_usage()
    data["temp"] = get_device_temp()
    data["uptime"] = get_system_uptime()
    data["is_installing_docker_images"] = is_installing_docker_images()
    data["is_electrs_active"] = is_electrs_active()

    return jsonify(data)

@mynode_api.route("/api/homepage_needs_refresh")
def api_homepage_needs_refresh():
    check_logged_in()

    data = {"needs_refresh": "no"}
    if get_mynode_status() != STATE_STABLE:
        data["needs_refresh"] = "yes"
    if not has_product_key() and not skipped_product_key():
        data["needs_refresh"] = "yes"
    if not get_has_updated_btc_info():
        data["needs_refresh"] = "yes"
    if not is_bitcoin_synced():
        data["needs_refresh"] = "yes"

    # If file indicating refresh was made, refresh and remove file
    if os.path.isfile("/tmp/homepage_needs_refresh"):
        data["needs_refresh"] = "yes"
        os.system("rm /tmp/homepage_needs_refresh")

    return jsonify(data)

@mynode_api.route("/api/get_log")
def api_get_log():
    check_logged_in()

    data = {"log": "LOG MISSING"}
    if not request.args.get("app"):
        data["log"] = "NO APP SPECIFIED"
        return jsonify(data)

    app_name = request.args.get("app")
    data["log"] = get_application_log(app_name)

    return jsonify(data)

@mynode_api.route("/api/get_qr_code_image")
def api_get_qr_code_image():
    check_logged_in()

    url = request.args.get("url") if request.args.get("url") else "ERROR_URL"
    img_buf = BytesIO() if isPython3() else cStringIO.StringIO()
    img = generate_qr_code(url)
    img.save(img_buf)
    img_buf.seek(0)
    return send_file(img_buf, mimetype='image/png')

@mynode_api.route("/api/get_message")
def api_get_message():
    check_logged_in()

    funny = bool(request.args.get("funny"))
    data = {"message": get_message(funny)}
    return jsonify(data)

@mynode_api.route("/api/toggle_setting")
def api_toggle_setting():
    check_logged_in()

    data = {"status": "unknown"}
    if not request.args.get("setting"):
        data["status"] = "no_setting_specified"
        return jsonify(data)

    setting = request.args.get("setting")
    if setting == "pinned_bitcoin_details":
        toggle_ui_setting("pinned_bitcoin_details")
        data["status"] = "success"
    elif setting == "pinned_lightning_details":
        toggle_ui_setting("pinned_lightning_details")
        data["status"] = "success"
    else:
        data["status"] = "unknown_setting"

    return jsonify(data)

@mynode_api.route("/api/set_setting")
def api_set_setting():
    check_logged_in()

    data = {"status": "unknown"}
    if not request.args.get("setting"):
        data["status"] = "no_setting_specified"
        return jsonify(data)
    if not request.args.get("value"):
        data["status"] = "no_value_specified"
        return jsonify(data)

    setting = request.args.get("setting")
    value = request.args.get("value")
    if setting == "format_filesystem_type":
        set_drive_filesystem_type(value)
        data["status"] = "success"
    else:
        data["status"] = "unknown_setting"

    return jsonify(data)

@mynode_api.route("/api/get_drive_benchmark")
def api_get_drive_benchmark():
    check_logged_in()

    data = {"status": "error", "data": "UNKNOWN"}
    try:
        data["data"] = to_string(subprocess.check_output("hdparm -Tt $(cat /tmp/.mynode_drive)", shell=True))
        data["status"] = "success"
    except Exception as e:
        data["data"] = str(e)
    return jsonify(data)

@mynode_api.route("/api/get_usb_info")
def api_get_usb_info():
    check_logged_in()

    data = {"status": "error", "data": "UNKNOWN"}
    try:
        info = ""
        info += to_string(subprocess.check_output("lsusb", shell=True))
        info += "\n\n"
        info += to_string(subprocess.check_output("lsusb -t", shell=True))
        data["data"] = info
        data["status"] = "success"
    except Exception as e:
        data["data"] = str(e)
    return jsonify(data)