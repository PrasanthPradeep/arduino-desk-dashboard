from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.metrics import (
    get_dashboard_data,
    get_services_info,
    get_system_details,
    load_services_config,
    save_services_config,
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
