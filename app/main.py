from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.metrics import (
    get_dashboard_data,
    get_services_info,
    get_system_details,
    get_all_block_devices,
    load_services_config,
    save_services_config,
    load_drives_config,
    save_drives_config,
)


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="Homeserver Dashboard",
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.get("/", response_class=HTMLResponse)
def root():
    template = (
        BASE_DIR / "templates" / "dashboard.html"
    )

    return template.read_text(
        encoding="utf-8"
    )


@app.get("/api/dashboard")
def dashboard():
    return get_dashboard_data()


@app.get("/api/system")
def system():
    data = get_dashboard_data()
    return data["system"]


@app.get("/api/smart")
def smart():
    data = get_dashboard_data()
    return data["smart"]


@app.get("/api/network")
def network():
    data = get_dashboard_data()
    return data["network"]


@app.get("/api/arduino")
def arduino():
    data = get_dashboard_data()
    return data["arduino"]


@app.get("/api/system-info")
def system_info():
    return get_system_details()


@app.get("/api/services")
def services():
    return get_services_info()


@app.get("/api/services/config")
def services_config():
    return load_services_config()


@app.post("/api/services/config/toggle-show-all")
def toggle_show_all():
    config = load_services_config()
    config["show_all"] = not config.get("show_all", False)
    save_services_config(config)
    return {"show_all": config["show_all"]}


@app.post("/api/services/config/add")
def add_service(service_name: str, display_name: str):
    config = load_services_config()
    config["services"][service_name] = display_name
    save_services_config(config)
    return config


@app.post("/api/services/config/remove")
def remove_service(service_name: str):
    config = load_services_config()
    config["services"].pop(service_name, None)
    save_services_config(config)
    return config


# ============================================================
# DRIVES CONFIG ENDPOINTS
# ============================================================

@app.get("/api/drives/config")
def drives_config():
    return load_drives_config()


@app.get("/api/drives/discover")
def discover_drives():
    return get_all_block_devices()


@app.post("/api/drives/config/add")
def add_drive(serial: str, display_name: str, mount: str):
    config = load_drives_config()
    config["drives"][serial] = {
        "display_name": display_name,
        "mount": mount,
    }
    save_drives_config(config)
    return config


@app.post("/api/drives/config/remove")
def remove_drive(serial: str):
    config = load_drives_config()
    config["drives"].pop(serial, None)
    save_drives_config(config)
    return config
