import json
import os
import platform
import re
import subprocess
import time
from pathlib import Path

import psutil


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICES_CONFIG_PATH = BASE_DIR / "services.json"
DRIVES_CONFIG_PATH = BASE_DIR / "drives.json"

SMART_WRAPPER = "/usr/local/sbin/arduino-desk-smartctl"

# SMART is intentionally not queried every dashboard refresh.
SMART_INTERVAL = 1800  # 30 minutes


# ============================================================
# SERVICES CONFIG
# ============================================================

def load_services_config():
    """Load services configuration from JSON file."""
    try:
        if SERVICES_CONFIG_PATH.exists():
            with open(SERVICES_CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass

    return {
        "show_all": False,
        "services": {
            "homeserverDashboard": "Homeserver Dashboard",
            "ssh": "SSH Server",
            "docker": "Docker",
        },
    }


def save_services_config(config):
    """Save services configuration to JSON file."""
    with open(SERVICES_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


# ============================================================
# DRIVES CONFIG
# ============================================================

def load_drives_config():
    """Load drives configuration from JSON file."""
    try:
        if DRIVES_CONFIG_PATH.exists():
            with open(DRIVES_CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass

    config = auto_detect_drives()
    save_drives_config(config)
    return config


def auto_detect_drives():
    """Auto-detect drives on first run and create config."""
    devices = get_lsblk_info()

    drives = {}
    for name, info in devices.items():
        key = info["serial"] if info["serial"] else name
        drives[key] = {
            "display_name": info["model"] or name,
            "mount": info["mountpoint"],
        }

    return {"drives": drives}


def save_drives_config(config):
    """Save drives configuration to JSON file."""
    with open(DRIVES_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def get_lsblk_info():
    """Get drive info from lsblk including partitions for mountpoints."""
    try:
        result = subprocess.run(
            [
                "lsblk",
                "-o",
                "NAME,SIZE,SERIAL,MODEL,TRAN",
                "-b",
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        mountpoints = get_mountpoints()

        if result.returncode == 0:
            data = json.loads(result.stdout)
            devices = {}

            for dev in data.get("blockdevices", []):
                name = dev.get("name", "")
                serial = str(dev.get("serial", None) or "").strip()
                size_raw = dev.get("size", "") or ""
                size = str(size_raw).strip() if size_raw else ""
                model = str(dev.get("model", None) or "").strip()
                tran = str(dev.get("tran", None) or "").strip()

                if name.startswith("loop"):
                    continue

                if tran == "loop":
                    continue

                mountpoint = mountpoints.get(name, "")

                if not mountpoint:
                    for part in dev.get("children", []):
                        part_name = part.get("name", "")
                        if part_name in mountpoints:
                            mountpoint = mountpoints[part_name]
                            break

                devices[name] = {
                    "serial": serial,
                    "size": size,
                    "model": model,
                    "mountpoint": mountpoint,
                }

            return devices

    except Exception:
        pass

    return {}


def get_mountpoints():
    """Get device -> mountpoint mapping from /proc/mounts."""
    mounts = {}
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    device = parts[0]
                    mountpoint = parts[1]
                    if device.startswith("/dev/"):
                        dev_name = device.replace("/dev/", "")
                        mounts[dev_name] = mountpoint
    except Exception:
        pass
    return mounts


def resolve_drive_device(key):
    """Resolve a serial number or device name to /dev/ path."""
    devices = get_lsblk_info()

    for name, info in devices.items():
        if info["serial"] and info["serial"] == key:
            return f"/dev/{name}"

    if key in devices:
        return f"/dev/{key}"

    return None


def get_all_block_devices():
    """Get all block devices for discovery."""
    devices = get_lsblk_info()

    result = {}
    for name, info in devices.items():
        key = info["serial"] if info["serial"] else name
        result[key] = {
            "device": f"/dev/{name}",
            "name": name,
            "size": info["size"],
            "model": info["model"],
            "has_serial": bool(info["serial"]),
        }

    return result


def get_all_active_services():
    """Auto-detect all active systemd services."""
    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=active",
                "--no-pager",
                "--no-legend",
                "--plain",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        services = {}
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 1:
                unit = parts[0]
                if unit.endswith(".service"):
                    name = unit[:-8]
                    services[name] = name.replace("-", " ").title()

        return services

    except Exception:
        return {}


# ============================================================
# SMART CACHE
# ============================================================

_smart_cache = {
    "sda": None,
    "sdb": None,
}

_smart_last_update = 0


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():
    memory = psutil.virtual_memory()

    # --------------------------------------------------------
    # Aggregate storage across configured drives.
    # --------------------------------------------------------

    config = load_drives_config()
    drives = config.get("drives", {})
    storage_filesystems = []

    for serial, drive_config in drives.items():
        mountpoint = drive_config.get("mount")
        if mountpoint:
            try:
                usage = psutil.disk_usage(mountpoint)
                storage_filesystems.append(usage)
            except Exception:
                pass

    storage_total = sum(
        usage.total
        for usage in storage_filesystems
    )

    storage_used = sum(
        usage.used
        for usage in storage_filesystems
    )

    storage_free = sum(
        usage.free
        for usage in storage_filesystems
    )

    storage_usage = (
        (storage_used / storage_total) * 100
        if storage_total
        else None
    )

    return {
        "cpu_usage": psutil.cpu_percent(interval=None),

        "ram_usage": memory.percent,

        "ram_used_gb": round(
            memory.used / (1024 ** 3),
            2,
        ),

        "ram_total_gb": round(
            memory.total / (1024 ** 3),
            2,
        ),

        "storage_usage": (
            round(storage_usage, 1)
            if storage_usage is not None
            else None
        ),

        "storage_used_gb": round(
            storage_used / (1024 ** 3),
            2,
        ),

        "storage_free_gb": round(
            storage_free / (1024 ** 3),
            2,
        ),

        "storage_total_gb": round(
            storage_total / (1024 ** 3),
            2,
        ),
    }


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_details():
    """
    Return static/general information about the server.
    """

    try:
        uptime_seconds = (
            time.time() - psutil.boot_time()
        )
    except Exception:
        uptime_seconds = None

    try:
        cpu_model = platform.processor()

        if not cpu_model:
            cpu_model = "Unknown"

        # On some Linux systems platform.processor() can be empty.
        if cpu_model == "Unknown":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            cpu_model = (
                                line.split(":", 1)[1].strip()
                            )
                            break
            except Exception:
                pass

    except Exception:
        cpu_model = "Unknown"

    return {
        "hostname": platform.node(),
        "os": platform.system(),
        "os_release": platform.release(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "cpu_model": cpu_model,
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True),
        "uptime_seconds": (
            round(uptime_seconds, 1)
            if uptime_seconds is not None
            else None
        ),
        "boot_time": psutil.boot_time(),
    }


# ============================================================
# SERVICE MONITORING
# ============================================================


def get_service_status(service_name):
    """
    Get the current systemd state of one service.
    """

    try:
        result = subprocess.run(
            [
                "systemctl",
                "is-active",
                service_name,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        state = result.stdout.strip()

        return {
            "name": service_name,
            "status": state or "unknown",
            "active": state == "active",
        }

    except Exception:
        return {
            "name": service_name,
            "status": "unknown",
            "active": False,
        }


def get_services_info():
    """
    Return the status of important server services.
    """

    config = load_services_config()
    show_all = config.get("show_all", False)

    if show_all:
        monitored = get_all_active_services()
    else:
        monitored = config.get("services", {})

    services = {}

    for service_name, display_name in monitored.items():
        data = get_service_status(service_name)

        services[service_name] = {
            "name": display_name,
            "status": data["status"],
            "active": data["active"],
        }

    active_count = sum(
        1
        for service in services.values()
        if service["active"]
    )

    return {
        "services": services,
        "total": len(services),
        "active": active_count,
        "inactive": len(services) - active_count,
        "show_all": show_all,
    }


# ============================================================
# CPU TEMPERATURE
# ============================================================

def get_cpu_temperature():
    try:
        sensors = psutil.sensors_temperatures()

        if "coretemp" not in sensors:
            return None

        entries = sensors["coretemp"]

        for entry in entries:
            if entry.label.lower() == "package id 0":
                return round(entry.current, 1)

        if entries:
            return round(
                max(entry.current for entry in entries),
                1,
            )

    except Exception:
        pass

    return None


# ============================================================
# SMART COMMAND
# ============================================================

def run_smart(args, device):
    try:
        result = subprocess.run(
            [
                "/usr/bin/sudo",
                "-n",
                SMART_WRAPPER,
                *args,
                device,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        # smartctl uses non-zero exit codes to report SMART
        # conditions such as failed self-tests. The output can
        # still contain valid and important SMART information.
        #
        # Therefore, return stdout whenever smartctl produced it.
        if result.stdout:
            return result.stdout

        return None

    except Exception:
        return None

# ============================================================
# SMART INFORMATION
# ============================================================

def parse_device_info(device):
    output = run_smart(["-i"], device)

    if output is None:
        return {
            "model": None,
            "serial": None,
            "capacity": None,
            "capacity_gb": None,
        }

    model = None
    serial = None
    capacity = None
    capacity_gb = None

    for line in output.splitlines():
        line = line.strip()

        if line.startswith("Device Model:"):
            model = line.split(":", 1)[1].strip()

        elif line.startswith("Model Number:") and model is None:
            model = line.split(":", 1)[1].strip()

        elif line.startswith("Serial Number:"):
            serial = line.split(":", 1)[1].strip()

        elif line.startswith("User Capacity:"):
            capacity = line.split(":", 1)[1].strip()

            match = re.search(
                r"([\d,]+)\s+bytes",
                capacity,
            )

            if match:
                try:
                    capacity_bytes = int(
                        match.group(1).replace(",", "")
                    )

                    capacity_gb = round(
                        capacity_bytes / (1000 ** 3),
                        1,
                    )
                except ValueError:
                    pass

    return {
        "model": model,
        "serial": serial,
        "capacity": capacity,
        "capacity_gb": capacity_gb,
    }


# ============================================================
# SMART ATTRIBUTES
# ============================================================

def parse_smart_attributes(attribute_output):
    attributes = {}

    if attribute_output is None:
        return attributes

    for line in attribute_output.splitlines():
        parts = line.split()

        if len(parts) < 10:
            continue

        try:
            attribute_id = int(parts[0])
        except ValueError:
            continue

        # Standard SMART table:
        #
        # ID
        # ATTRIBUTE_NAME
        # FLAG
        # VALUE
        # WORST
        # THRESH
        # TYPE
        # UPDATED
        # WHEN_FAILED
        # RAW_VALUE

        raw_value = parts[9]

        match = re.match(r"(\d+)", raw_value)

        if match:
            attributes[attribute_id] = int(
                match.group(1)
            )

    return attributes


# ============================================================
# SELF-TEST INFORMATION
# ============================================================

def parse_self_test_status(device):
    output = run_smart(["-l", "selftest"], device)

    result = {
        "status": "UNKNOWN",
        "test": None,
        "remaining_percent": None,
        "lba": None,
    }

    if output is None:
        return result

    for line in output.splitlines():
        line = line.strip()

        if not line.startswith("#"):
            continue

        parts = line.split()

        # Expected format:
        #
        # # 1 Extended offline Completed: read failure 90% 163 1916819068
        #
        # Index:
        # 0 = #
        # 1 = test number
        # 2 = test type
        # 3... = status
        # N = remaining %
        # N+1 = lifetime hours
        # N+2 = LBA

        if len(parts) < 6:
            continue

        # Find remaining percentage.
        remaining_index = None

        for i, value in enumerate(parts):
            if re.fullmatch(r"\d+%", value):
                remaining_index = i
                break

        if remaining_index is None:
            continue

        # Test description is normally two words:
        # "Extended offline"
        # "Short offline"
        test = " ".join(parts[2:4])

        # Status comes after test description.
        status_start = 4

        status = " ".join(
            parts[status_start:remaining_index]
        ).strip()

        try:
            remaining_percent = int(
                parts[remaining_index].rstrip("%")
            )
        except ValueError:
            continue

        lba = None

        if len(parts) > remaining_index + 2:
            possible_lba = parts[remaining_index + 2]

            if possible_lba != "-":
                lba = possible_lba

        result = {
            "status": status,
            "test": test,
            "remaining_percent": remaining_percent,
            "lba": lba,
        }

        # First row is the most recent test.
        break

    return result


# ============================================================
# DASHBOARD HEALTH ASSESSMENT
# ============================================================

def calculate_drive_assessment(
    smart_health,
    reallocated,
    pending,
    offline_uncorrectable,
    crc_errors,
):
    reasons = []

    if smart_health == "BAD":
        return {
            "level": "CRITICAL",
            "label": "Critical",
            "reasons": [
                "SMART overall health has failed."
            ],
        }

    if offline_uncorrectable is not None:
        if offline_uncorrectable > 0:
            reasons.append(
                f"{offline_uncorrectable} offline "
                "uncorrectable sector(s)."
            )

    if pending is not None:
        if pending > 0:
            reasons.append(
                f"{pending} current pending sector(s)."
            )

    if reasons:
        return {
            "level": "CRITICAL",
            "label": "Critical",
            "reasons": reasons,
        }

    warning_reasons = []

    if reallocated is not None:
        if reallocated > 0:
            warning_reasons.append(
                f"{reallocated} sector(s) have been reallocated."
            )

    if crc_errors is not None:
        if crc_errors > 0:
            warning_reasons.append(
                f"{crc_errors} UDMA CRC error(s) recorded."
            )

    if warning_reasons:
        return {
            "level": "WARNING",
            "label": "Warning",
            "reasons": warning_reasons,
        }

    return {
        "level": "HEALTHY",
        "label": "Healthy",
        "reasons": [],
    }


# ============================================================
# HDD SMART DATA
# ============================================================

def parse_smart(device, mountpoint=None):
    device_info = parse_device_info(device)

    # Filesystem usage for this physical drive.
    filesystem = None

    if mountpoint:
        try:
            usage = psutil.disk_usage(mountpoint)

            filesystem = {
                "mountpoint": mountpoint,
                "total_gb": round(
                    usage.total / (1024 ** 3),
                    2,
                ),
                "used_gb": round(
                    usage.used / (1024 ** 3),
                    2,
                ),
                "free_gb": round(
                    usage.free / (1024 ** 3),
                    2,
                ),
                "usage_percent": round(
                    usage.percent,
                    1,
                ),
            }

        except Exception:
            pass

    health_output = run_smart(["-H"], device)
    attribute_output = run_smart(["-A"], device)

    if health_output is None or attribute_output is None:
        return {
            **device_info,

            "temperature": None,

            "health": "UNKNOWN",

            "assessment": {
                "level": "UNKNOWN",
                "label": "Unknown",
                "reasons": [
                    "Unable to read SMART data."
                ],
            },

            "reallocated": None,
            "pending": None,
            "offline_uncorrectable": None,
            "crc_errors": None,

            "self_test": {
                "status": "UNKNOWN",
                "remaining_percent": None,
                "lba": None,
            },
        }

    output_upper = health_output.upper()

    if "PASSED" in output_upper:
        health = "OK"
    elif "FAILED" in output_upper:
        health = "BAD"
    else:
        health = "UNKNOWN"

    attributes = parse_smart_attributes(
        attribute_output
    )

    temperature = None

    if 194 in attributes:
        temperature = attributes[194]

    if temperature is None and 190 in attributes:
        temperature = attributes[190]

    reallocated = attributes.get(5)
    pending = attributes.get(197)
    offline_uncorrectable = attributes.get(198)
    crc_errors = attributes.get(199)

    assessment = calculate_drive_assessment(
        health,
        reallocated,
        pending,
        offline_uncorrectable,
        crc_errors,
    )

    return {
    **device_info,

    # Filesystem usage.
    "filesystem": filesystem,

    "temperature": temperature,

    # Raw SMART result.
    "health": health,

    # Dashboard interpretation.
    "assessment": assessment,

    "reallocated": reallocated,
    "pending": pending,
    "offline_uncorrectable": offline_uncorrectable,
    "crc_errors": crc_errors,

    "self_test": parse_self_test_status(device),
}


# ============================================================
# SMART CACHE UPDATE
# ============================================================

def update_smart_cache(force=False):
    global _smart_last_update

    now = time.time()

    if (
        not force
        and _smart_last_update
        and now - _smart_last_update < SMART_INTERVAL
    ):
        return

    config = load_drives_config()
    drives = config.get("drives", {})

    for serial, drive_config in drives.items():
        device = resolve_drive_device(serial)
        mountpoint = drive_config.get("mount")

        if device:
            _smart_cache[serial] = parse_smart(device, mountpoint)
        else:
            _smart_cache[serial] = {
                "connected": False,
                "display_name": drive_config.get("display_name", serial),
                "assessment": {
                    "level": "DISCONNECTED",
                    "label": "Disconnected",
                    "reasons": ["Drive not found."],
                },
            }

    _smart_last_update = now


def get_smart_info():
    update_smart_cache()

    return {
        "last_updated": _smart_last_update,
        "interval_seconds": SMART_INTERVAL,
        "drives": _smart_cache,
    }


# ============================================================
# NETWORK
# ============================================================

def ping_host(host):
    try:
        result = subprocess.run(
            [
                "ping",
                "-c",
                "1",
                "-W",
                "3",
                host,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        match = re.search(
            r"time[=<]([\d.]+)",
            result.stdout,
        )

        if match:
            return float(match.group(1))

    except Exception:
        pass

    return None


def get_network_info():
    internet_ping = ping_host("8.8.8.8")
    router_ping = ping_host("192.168.1.1")

    return {
        "internet_ping_ms": (
            round(internet_ping, 1)
            if internet_ping is not None
            else None
        ),

        "router_ping_ms": (
            round(router_ping, 1)
            if router_ping is not None
            else None
        ),

        "internet_status": (
            "ONLINE"
            if internet_ping is not None
            else "OFFLINE"
        ),

        "router_status": (
            "ONLINE"
            if router_ping is not None
            else "OFFLINE"
        ),
    }


# ============================================================
# ARDUINO SERVICE
# ============================================================

def get_arduino_service_status():
    try:
        result = subprocess.run(
            [
                "/usr/bin/systemctl",
                "is-active",
                "arduino-desk.service",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        status = result.stdout.strip()

        return {
            "status": status,
            "active": status == "active",
        }

    except Exception:
        return {
            "status": "unknown",
            "active": False,
        }


# ============================================================
# COMPLETE DASHBOARD SNAPSHOT
# ============================================================

def get_dashboard_data():
    system = get_system_info()

    system["cpu_temperature"] = get_cpu_temperature()

    return {
        "timestamp": time.time(),
        "system": system,
        "smart": get_smart_info(),
        "network": get_network_info(),
        "arduino": get_arduino_service_status(),
    }
