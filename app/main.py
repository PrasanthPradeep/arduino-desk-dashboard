from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.metrics import (
    get_dashboard_data,
    get_services_info,
    get_system_details,
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


@app.get("/manifest.json")
def manifest():
    manifest_path = BASE_DIR / "static" / "manifest.json"
    return JSONResponse(
        content=manifest_path.read_text(encoding="utf-8"),
        media_type="application/manifest+json",
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
