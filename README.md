# Homeserver Dashboard

A lightweight, self-hosted web dashboard for monitoring and managing a Linux home server.

The dashboard provides a single web interface for viewing system information, resource usage, storage health, network connectivity, monitored services, and Arduino-based desk display status.

It is designed to run on a small home server with minimal hardware and without requiring a desktop environment.

---

## Features

### System Monitoring

The dashboard displays:

- Hostname
- Operating system
- OS release
- Linux kernel version
- CPU model
- CPU core count
- CPU thread count
- System uptime
- Boot time
- CPU usage
- RAM usage
- Storage usage
- CPU temperature

### Storage Monitoring

SMART information is collected for configured drives, including:

- Drive model
- Serial number
- Capacity
- Filesystem usage
- Drive temperature
- SMART health
- Reallocated sectors
- Current pending sectors
- Offline uncorrectable sectors
- UDMA CRC errors
- Latest SMART self-test result
- Self-test failure LBA when available

The dashboard also performs an assessment of drive health and can distinguish between normal, warning, and critical conditions.

Drives are configured via `drives.json` and can be managed from the dashboard UI.

On first run, drives are auto-detected using `lsblk` and `/proc/mounts`.

### Network Monitoring

The dashboard monitors:

- Internet connectivity
- Internet latency
- Router connectivity
- Router latency

Example status:

```text
Internet: ONLINE
Ping: 20.9 ms

Router: ONLINE
Ping: 0.6 ms
```

### Service Monitoring

The dashboard monitors Linux systemd services using a hybrid approach:

**Curated List:** A default set of important services configured in `services.json`.

**Show All Mode:** Auto-detects all active systemd services with a toggle button.

The default curated configuration includes:

* Homeserver Dashboard
* Arduino Desk Display
* SSH Server
* Docker
* SMART Monitoring
* Samba SMB
* Samba NetBIOS
* Tailscale

Services can be added to or removed from the curated list directly from the dashboard UI.

### Arduino Integration

The dashboard can monitor the status of the Arduino desk display service.

This allows the web dashboard and physical desk display to provide complementary information about the server.

### Automatic Refresh

Dashboard data is refreshed automatically without requiring a manual browser refresh.

The main dashboard currently refreshes every 5 seconds.

### Lightweight

The application is built around:

* Python
* FastAPI
* Uvicorn
* HTML
* CSS
* JavaScript
* psutil
* smartmontools
* systemd

It does not require a heavy frontend framework.

---

## Architecture

The project follows a simple server-side API + browser frontend architecture.

```text
                         ┌───────────────────────┐
                         │       Browser         │
                         │                       │
                         │ HTML / CSS / JS       │
                         └───────────┬───────────┘
                                     │
                                     │ HTTP
                                     ▼
                         ┌───────────────────────┐
                         │       FastAPI         │
                         │       Uvicorn         │
                         │                       │
                         │     app/main.py       │
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
               System APIs      Service APIs     SMART APIs
                    │                │                │
                    ▼                ▼                ▼
                  psutil           systemd       smartctl
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                                     ▼
                              Linux Home Server
```

---

## Project Structure

The production project should contain only the files required to run the application.

```text
homeserverDashboard/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── metrics.py
│   │
│   ├── static/
│   │   ├── dashboard.css
│   │   └── dashboard.js
│   │
│   └── templates/
│       └── dashboard.html
│
├── services.json           # Service monitoring config (auto-managed)
├── drives.json             # Drive monitoring config (auto-generated)
├── .gitignore
├── README.md
├── requirements.txt
├── setup-local.sh        # Local development setup
├── setup.sh              # Full production setup (requires sudo)
└── venv/                 # Local only, not committed
```

The virtual environment should never be committed to Git.

---

## Technology Stack

### Python

The application backend is written in Python.

Python is responsible for:

* Starting the web server
* Collecting system information
* Reading system metrics
* Querying SMART information
* Checking systemd services
* Providing JSON APIs
* Rendering the dashboard

### FastAPI

FastAPI provides the HTTP API and dashboard backend.

### Uvicorn

Uvicorn runs the FastAPI application.

The production service runs Uvicorn using the project's Python virtual environment.

---

## Frontend

The frontend uses standard web technologies:

* HTML
* CSS
* JavaScript

No Node.js build process is required for the dashboard frontend.

The browser communicates with the backend using HTTP API endpoints.

---

## System Dependencies

The dashboard is intended primarily for Linux systems.

The following system components are required or recommended:

* Python 3
* pip
* systemd
* smartmontools
* sudo
* psutil
* FastAPI
* Uvicorn

Additional system services such as Docker, Samba, Tailscale, or an Arduino service are optional and can be added to the monitoring configuration.

---

## Requirements

Recommended environment:

```text
Linux
Python 3.10+
systemd
smartmontools
sudo
```

The application can run on relatively low-powered hardware.

For example, a small home server with:

```text
2 CPU cores
4 CPU threads
~6 GB RAM
HDD storage
```

is sufficient for this type of monitoring workload.

---

## Installation

### 1. Clone the Repository

Clone the repository to the location where you want to run the dashboard.

Example:

```bash
git clone git@github.com:PrasanthPradeep/arduino-desk-dashboard.git
```

Or using HTTPS:

```bash
git clone https://github.com/PrasanthPradeep/arduino-desk-dashboard.git
```

Enter the project directory:

```bash
cd homeserverDashboard
```

> Replace `homeserverDashboard` with the directory name used on your system.

---

### 2. Create a Python Virtual Environment

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

You should see something similar to:

```text
(venv) user@server:~/homeserverDashboard$
```

---

### 3. Install Python Dependencies

Install the required packages:

```bash
pip install --upgrade pip
```

Then install the application dependencies:

```bash
pip install fastapi uvicorn psutil
```

If the repository contains a `requirements.txt` file, use:

```bash
pip install -r requirements.txt
```

instead.

---

### 4. Install SMART Monitoring

Install `smartmontools`.

On Debian/Ubuntu:

```bash
sudo apt update
sudo apt install smartmontools
```

Verify:

```bash
smartctl --version
```

---

### 5. Test SMART Access

Check a drive manually:

```bash
sudo smartctl -A /dev/sda
```

For a second drive:

```bash
sudo smartctl -A /dev/sdb
```

Check the SMART self-test history:

```bash
sudo smartctl -l selftest /dev/sda
```

Your drive device names may be different.

Check them with:

```bash
lsblk
```

---

### 6. Configure SMART Permissions

The dashboard may need elevated privileges to execute SMART commands.

A recommended approach is to use a narrowly scoped `sudoers` configuration or a dedicated privileged helper instead of allowing the entire application to run as root.

For example, the system can expose a restricted SMART helper such as:

```text
/usr/local/sbin/arduino-desk-smartctl
```

The helper can then be explicitly permitted through sudo.

Do not give the dashboard unrestricted root access unless there is a specific reason to do so.

---

## Running the Application Manually

Activate the virtual environment:

```bash
source venv/bin/activate
```

Start the application:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The dashboard will listen on:

```text
http://0.0.0.0:8000
```

From the same server:

```text
http://127.0.0.1:8000
```

From another device on the LAN:

```text
http://SERVER_IP:8000
```

Find the server IP using:

```bash
ip addr
```

or:

```bash
hostname -I
```

---

## Running as a systemd Service

For a home server, running the dashboard as a systemd service is recommended.

Create:

```text
/etc/systemd/system/homeserverDashboard.service
```

Example:

```ini
[Unit]
Description=Homeserver Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple

User=prashu
Group=prashu

WorkingDirectory=/opt/homeserverDashboard

ExecStart=/opt/homeserverDashboard/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=5

Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Change the following values for your system:

```text
User=
Group=
WorkingDirectory=
ExecStart=
```

---

## Enable the Service

After creating or modifying the systemd unit:

```bash
sudo systemctl daemon-reload
```

Enable it at boot:

```bash
sudo systemctl enable homeserverDashboard
```

Start it:

```bash
sudo systemctl start homeserverDashboard
```

Check its status:

```bash
sudo systemctl status homeserverDashboard --no-pager -l
```

A successful service should show:

```text
Active: active (running)
```

---

## Restarting the Dashboard

After changing application code:

```bash
sudo systemctl restart homeserverDashboard
```

Then verify:

```bash
sudo systemctl status homeserverDashboard --no-pager -l
```

---

## Viewing Logs

View recent logs:

```bash
sudo journalctl -u homeserverDashboard -n 100 --no-pager
```

Follow logs live:

```bash
sudo journalctl -u homeserverDashboard -f
```

---

## API

The dashboard exposes several internal HTTP endpoints.

### System Information

```http
GET /api/system-info
```

### Services API

```http
GET /api/services
```

### Services Configuration

```http
GET  /api/services/config
POST /api/services/config/toggle-show-all
POST /api/services/config/add?service_name=X&display_name=Y
POST /api/services/config/remove?service_name=X
```

### Drives Configuration

```http
GET  /api/drives/config
GET  /api/drives/discover
POST /api/drives/config/add?serial=X&display_name=Y&mount=Z
POST /api/drives/config/remove?serial=X
```

### Dashboard API

```http
GET /api/dashboard
```

This endpoint provides the combined dashboard data including system, SMART, network, and Arduino information.

---

## Testing the APIs

Test the system information endpoint:

```bash
curl -s http://127.0.0.1:8000/api/system-info | python -m json.tool
```

Test services:

```bash
curl -s http://127.0.0.1:8000/api/services | python -m json.tool
```

Test the complete dashboard:

```bash
curl -s http://127.0.0.1:8000/api/dashboard | python -m json.tool
```

Test the HTML page:

```bash
curl -s http://127.0.0.1:8000/
```

---

## Service Monitoring Configuration

Services are configured in `services.json`:

```json
{
    "show_all": false,
    "services": {
        "homeserverDashboard": "Homeserver Dashboard",
        "arduino-desk": "Arduino Desk Display",
        "ssh": "SSH Server",
        "docker": "Docker",
        "smartmontools": "SMART Monitoring",
        "smbd": "Samba SMB",
        "nmbd": "Samba NetBIOS",
        "tailscaled": "Tailscale"
    }
}
```

### Curated Mode

The dashboard shows only services listed in the `services` dictionary.

### Show All Mode

Toggle "Show All" in the dashboard to auto-detect all active systemd services.

In this mode, you can:
- Click **+** to add a service to the curated list
- Click **✓** (red) to remove a service from the curated list

### Adding a Service Manually

Edit `services.json` and add the service:

```json
"nginx": "Nginx Web Server"
```

The service must exist on the Linux system.

Check available services:

```bash
systemctl list-units --type=service
```

---

## Storage and SMART Monitoring

SMART monitoring is particularly important for a home server because storage failures can result in data loss.

### Drive Configuration

Drives are configured in `drives.json`:

```json
{
    "drives": {
        "785BMTYFS": {
            "display_name": "TOSHIBA HDWD110",
            "mount": "/srv/storage"
        },
        "Z6E8MK2F": {
            "display_name": "ST500DM002-1BD142",
            "mount": "/"
        }
    }
}
```

**Key points:**
- Drives are identified by serial number (stable across reboots)
- If no serial number exists, device name (e.g. `sda`) is used
- Mount points are auto-detected from `/proc/mounts` on first run
- Drives can be added/removed from the dashboard UI

### Auto-Detection

On first run (or when `drives.json` is empty), drives are auto-detected:
1. `lsblk` scans block devices
2. `/proc/mounts` provides mount points
3. `drives.json` is created automatically

### Manual Configuration

If auto-detection doesn't find the correct mount point:

1. Click **⚙** on the drive card
2. Enter the mount point (e.g. `/srv/storage`)
3. The dashboard will start monitoring that drive

### SMART Attributes

```text
Temperature
Reallocated sectors
Pending sectors
Offline uncorrectable sectors
UDMA CRC errors
Self-test status
```

### Important SMART Indicators

#### Reallocated Sectors

A non-zero value indicates that the drive has already remapped one or more problematic sectors.

Increasing values are a warning sign.

#### Current Pending Sectors

Pending sectors are sectors that the drive has difficulty reading and may need to remap.

A non-zero value should be investigated.

A rapidly increasing pending-sector count is particularly concerning.

#### Offline Uncorrectable

This indicates sectors that could not be corrected during an offline SMART operation.

Non-zero values should be investigated.

#### UDMA CRC Errors

CRC errors are commonly associated with communication problems between the drive and the host.

Possible causes include:

* SATA cable problems
* Poor connection
* Electrical interference
* Controller/port problems

A non-zero historical value does not necessarily mean the drive itself is failing.

---

## SMART Self Tests

A short SMART test can be started with:

```bash
sudo smartctl -t short /dev/sda
```

An extended test can be started with:

```bash
sudo smartctl -t long /dev/sda
```

Check the result:

```bash
sudo smartctl -l selftest /dev/sda
```

A long test can take a significant amount of time depending on the drive.

Do not repeatedly start long tests unnecessarily.

---

## Drive Temperature

Typical HDD temperatures depend on:

* Ambient temperature
* Case airflow
* Drive workload
* Drive model
* Drive position
* Number of drives in the enclosure

The dashboard reports the temperature provided by SMART.

For example:

```text
Temperature: 42°C
```

A temperature should be interpreted in the context of the drive manufacturer's specifications and the server's environment.

---

## Network Monitoring

The dashboard checks connectivity to the local router and the Internet.

The exact router target and Internet target depend on the implementation in `app/metrics.py`.

Example output:

```text
Router: ONLINE
Router ping: 0.6 ms

Internet: ONLINE
Internet ping: 20.9 ms
```

The dashboard uses latency as an additional indicator of connectivity.

A server may have Internet connectivity even when latency temporarily increases.

---

## Arduino Desk Display

The project can integrate with a separate Arduino-based desk display service.

The dashboard checks the corresponding systemd service:

```text
arduino-desk
```

The service is displayed as:

```text
Active
```

or:

```text
Inactive
```

The Arduino hardware itself is not required to run the web dashboard unless the corresponding integration is enabled.

---

## Security

The dashboard is designed for use on a trusted home network.

By default, Uvicorn is configured to listen on:

```text
0.0.0.0:8000
```

This means the dashboard can be accessed from other devices that can reach the server.

### Do Not Expose Port 8000 Directly to the Internet

Do not simply port-forward:

```text
8000
```

from your router to the server.

If remote access is required, use a secure solution such as:

* Tailscale
* VPN
* Reverse proxy with HTTPS and authentication
* Another properly secured remote-access mechanism

---

## Credentials and Secrets

The dashboard should not contain hardcoded:

```text
Passwords
API keys
Access tokens
Private keys
Bot tokens
SMTP passwords
Authorization headers
```

Secrets should never be committed to Git.

If environment variables are used in the future, store them in:

```text
.env
```

and ensure `.env` is included in `.gitignore`.

Example:

```env
API_TOKEN=replace_with_real_secret
```

Never commit the actual secret.

---

## Development

Clone the project:

```bash
git clone <repository-url>
cd homeserverDashboard
```

Create the virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install fastapi uvicorn psutil
```

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` option automatically reloads the application when Python source files change.

Do not normally use `--reload` for the production systemd service.

---

## Code Organization

### `app/main.py`

The main FastAPI application.

Responsibilities include:

* Application initialization
* Routes
* API endpoints
* Template rendering
* Static file configuration

---

### `app/metrics.py`

Contains system monitoring functionality.

Responsibilities include:

* CPU monitoring
* RAM monitoring
* Storage monitoring
* Temperature monitoring
* SMART data collection
* Network monitoring
* Service monitoring
* System information

Keeping monitoring logic separate from the HTTP application makes the project easier to maintain.

---

### `app/templates/dashboard.html`

Contains the dashboard page structure.

It defines:

* Dashboard sections
* System information
* Service cards
* Storage information
* Network information
* Arduino status
* Frontend element IDs

---

### `app/static/dashboard.css`

Contains the visual styling of the dashboard.

This includes:

* Layout
* Cards
* Typography
* Status indicators
* Responsive behavior
* Storage and system panels

---

### `app/static/dashboard.js`

Contains client-side dashboard functionality where applicable.

The browser uses JavaScript to communicate with the backend APIs and update dashboard values.

---

## Frontend Data Flow

The browser periodically requests data from the backend.

Example:

```text
Browser
   │
   │ GET /api/dashboard
   ▼
FastAPI
   │
   ▼
metrics.py
   │
   ├── psutil
   ├── smartctl
   ├── systemd
   └── network checks
   │
   ▼
JSON response
   │
   ▼
Browser
   │
   ▼
Dashboard updated
```

System information and service information can also be retrieved independently:

```text
GET /api/system-info
GET /api/services
```

---

## Troubleshooting

### Dashboard Does Not Start

Check the service:

```bash
sudo systemctl status homeserverDashboard --no-pager -l
```

View logs:

```bash
sudo journalctl -u homeserverDashboard -n 100 --no-pager
```

Try running manually:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### Port 8000 Already in Use

Check:

```bash
sudo ss -ltnp | grep ':8000'
```

Find the process:

```bash
ps aux | grep '[u]vicorn'
```

If another instance is running, stop it before starting another one.

If systemd manages the application, prefer:

```bash
sudo systemctl restart homeserverDashboard
```

rather than manually starting another Uvicorn process.

---

### API Returns No Data

First check that the service is running:

```bash
sudo systemctl is-active homeserverDashboard
```

Then test:

```bash
curl -s http://127.0.0.1:8000/api/dashboard
```

If the response is empty or invalid, check:

```bash
sudo journalctl -u homeserverDashboard -n 100 --no-pager
```

---

### SMART Information Is Missing

Check:

```bash
sudo smartctl -A /dev/sda
```

If this fails, verify:

```bash
lsblk
```

and confirm that the device path is correct.

Also check the configured SMART helper/sudo permissions.

---

### Dashboard Shows a Service as Inactive

First check the service directly:

```bash
systemctl status <service-name>
```

For example:

```bash
systemctl status docker
```

If the service does not exist:

```bash
systemctl list-units --type=service
```

Then either install/configure the required service or remove it from the monitored service list.

---

### Browser Cannot Connect

Verify the server is listening:

```bash
sudo ss -ltnp | grep ':8000'
```

Expected:

```text
0.0.0.0:8000
```

Test locally:

```bash
curl http://127.0.0.1:8000/
```

If local access works but another device cannot connect, check:

* Server IP address
* Firewall
* Router/network isolation
* Client network
* Port 8000 accessibility

---

## Testing Checklist

After installation, verify:

```bash
python -m py_compile app/main.py app/metrics.py
```

Check the service:

```bash
sudo systemctl is-active homeserverDashboard
```

Check the listening port:

```bash
sudo ss -ltnp | grep ':8000'
```

Check system information:

```bash
curl -s http://127.0.0.1:8000/api/system-info | python -m json.tool
```

Check services:

```bash
curl -s http://127.0.0.1:8000/api/services | python -m json.tool
```

Check services config:

```bash
curl -s http://127.0.0.1:8000/api/services/config | python -m json.tool
```

Check drives config:

```bash
curl -s http://127.0.0.1:8000/api/drives/config | python -m json.tool
```

Check dashboard:

```bash
curl -s http://127.0.0.1:8000/api/dashboard | python -m json.tool
```

Check HTML:

```bash
curl -s http://127.0.0.1:8000/ | head
```

---

## Updating the Application

If the repository is already cloned:

```bash
cd /opt/homeserverDashboard
```

Pull changes:

```bash
git pull
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Update Python dependencies if required:

```bash
pip install -r requirements.txt
```

Restart:

```bash
sudo systemctl restart homeserverDashboard
```

Verify:

```bash
sudo systemctl status homeserverDashboard --no-pager -l
```

---

## Making Changes

A recommended development workflow is:

```bash
git pull
```

Make changes.

Run syntax checks:

```bash
python -m py_compile app/main.py app/metrics.py
```

Test the application:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify the API:

```bash
curl -s http://127.0.0.1:8000/api/dashboard | python -m json.tool
```

Then commit:

```bash
git add .
git commit -m "feat: describe the change"
```

Push:

```bash
git push
```

---

## Commit Message Convention

Use conventional commit-style messages.

Examples:

```text
feat: add disk temperature monitoring
```

```text
fix: correct SMART self-test parsing
```

```text
docs: improve installation documentation
```

```text
refactor: separate network metrics from dashboard logic
```

```text
style: improve dashboard service cards
```

```text
chore: update Python dependencies
```

Recommended format:

```text
<type>: <short description>
```

Common types:

| Type       | Purpose               |
| ---------- | --------------------- |
| `feat`     | New functionality     |
| `fix`      | Bug fix               |
| `docs`     | Documentation         |
| `refactor` | Code restructuring    |
| `style`    | UI/formatting changes |
| `test`     | Tests                 |
| `chore`    | Maintenance           |

---

## Production Deployment

A recommended production setup is:

```text
Linux Server
    │
    ├── systemd
    │     └── homeserverDashboard.service
    │
    ├── Python virtual environment
    │     └── venv/
    │
    ├── FastAPI
    │     └── app/main.py
    │
    ├── Uvicorn
    │     └── :8000
    │
    ├── SMART monitoring
    │     └── smartctl
    │
    ├── system monitoring
    │     └── psutil
    │
    └── optional remote access
          └── Tailscale / VPN
```

The application should run under a dedicated non-root user whenever possible.

Only specific privileged operations, such as SMART access, should receive additional permissions.

---

## Reverse Proxy

For a larger deployment, the application can be placed behind a reverse proxy such as:

```text
Internet / LAN
      │
      ▼
Reverse Proxy
      │
      ▼
Uvicorn :8000
      │
      ▼
FastAPI
```

A reverse proxy can provide:

* HTTPS
* Domain names
* Access control
* Request logging
* Additional security controls

The application itself does not require a reverse proxy for a basic LAN deployment.

---

## Remote Access

For secure remote access to a home server, a private VPN/mesh network is recommended.

For example, Tailscale can provide access without exposing port 8000 directly to the public Internet.

A typical architecture:

```text
Laptop / Phone
      │
      │ Secure private network
      ▼
Tailscale
      │
      ▼
Home Server
      │
      ▼
Homeserver Dashboard :8000
```

---

## Performance

The dashboard is designed to have a low resource footprint.

Typical workload includes:

* Lightweight HTTP requests
* Periodic system metric collection
* SMART queries
* Service status checks
* Network latency checks

SMART operations can be more expensive than reading CPU or RAM metrics.

For this reason, SMART information can be cached rather than querying every drive on every browser refresh.

The dashboard can therefore refresh frequently while SMART information is updated less frequently.

---

## Data and Privacy

The dashboard is intended to operate locally on the server.

It does not inherently require an external database or cloud service.

The information displayed can include sensitive infrastructure information such as:

* Hostname
* Internal IP/network information
* Storage devices
* Drive serial numbers
* Running services
* System configuration

Therefore, access to the dashboard should be restricted to trusted users.

Do not expose it publicly without adding appropriate authentication and security controls.

---

## Backup Recommendations

The dashboard itself is not a backup system.

The server administrator should separately back up important data.

Recommended backup strategy:

```text
Primary storage
      │
      ├── Local backup
      │
      └── External/off-site backup
```

The dashboard's SMART monitoring can help detect storage problems, but SMART monitoring does not protect data from:

* Drive failure
* Accidental deletion
* Malware
* Filesystem corruption
* Theft
* Fire
* Hardware damage

---

## Future Improvements

Potential future improvements include:

* Authentication
* HTTPS support
* Historical metrics
* CPU usage graphs
* RAM usage graphs
* HDD temperature history
* Network latency graphs
* Disk health history
* Alerting
* Telegram notifications
* Email notifications
* ~~Configurable monitored services~~ (done)
* ~~Configurable monitored drives~~ (done)
* Docker container monitoring
* Disk-space alerts
* Temperature alerts
* SMART failure alerts
* Systemd failure alerts
* ~~Mobile-responsive improvements~~ (done)
* REST API documentation
* Automated tests
* Docker deployment
* Reverse-proxy configuration
* Role-based access
* Persistent metrics storage

---

## Development Principles

The project aims to follow a few simple principles:

### Keep the application lightweight

Avoid unnecessary frameworks and dependencies.

### Prefer standard Linux tooling

Use reliable Linux interfaces such as:

```text
systemd
smartctl
psutil
```

where appropriate.

### Avoid running the entire application as root

Only privileged operations should receive additional permissions.

### Keep frontend and backend responsibilities separated

The backend collects and provides data.

The frontend presents the data.

### Avoid hardcoded secrets

Credentials and tokens should never be committed to source control.

### Make the project easy to deploy

A new Linux user should be able to install and run the dashboard with a small number of commands.

---

## License

Add your preferred open-source license here.

For example:

```text
MIT License
```

If this repository does not yet have a license, replace this section with the license you intend to use before publishing the project as an open-source project.

---

## Author

**Prasanth P**

GitHub:

```text
https://github.com/PrasanthPradeep
```

Website:

```text
https://prasanthp.tech
```

---

## Project Status

The project is actively developed as a personal home-server monitoring dashboard.

Current functionality includes:

* System monitoring
* CPU monitoring
* RAM monitoring
* Storage monitoring
* HDD temperature monitoring
* SMART monitoring
* SMART self-test reporting
* Network monitoring
* systemd service monitoring (curated + show-all toggle)
* Configurable service list via JSON
* Auto-detected drive monitoring with serial-based tracking
* Add/remove drives from dashboard UI
* Arduino desk-display monitoring
* Automatic dashboard refresh
* Dark/light theme toggle
* Mobile-responsive design
* systemd deployment

---

## Quick Start

### Option 1: Local Setup (Recommended for Development)

```bash
git clone <repository-url>
cd homeserverDashboard

./setup-local.sh
```

This creates a virtual environment and installs Python dependencies without requiring root access.

Then run:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 2: Full Setup (Including systemd Service)

```bash
git clone <repository-url>
cd homeserverDashboard

./setup.sh
```

This installs system dependencies, creates a virtual environment, and configures the application as a systemd service.

Then open:

```text
http://SERVER_IP:8000
```

### Option 3: Manual Setup

```bash
git clone <repository-url>
cd homeserverDashboard

python3 -m venv venv
source venv/bin/activate

pip install fastapi uvicorn psutil

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a persistent production deployment, configure the application as a systemd service.

---

## Quick Health Check

After deployment:

```bash
sudo systemctl is-active homeserverDashboard
```

```bash
sudo ss -ltnp | grep ':8000'
```

```bash
curl -s http://127.0.0.1:8000/api/system-info | python -m json.tool
```

```bash
curl -s http://127.0.0.1:8000/api/services | python -m json.tool
```

```bash
curl -s http://127.0.0.1:8000/api/dashboard | python -m json.tool
```

If all commands return successfully and the service is active, open the dashboard in a browser:

```text
http://SERVER_IP:8000
```

---

## Summary

Homeserver Dashboard provides a lightweight, self-hosted monitoring interface for a Linux home server.

It combines:

```text
FastAPI
   +
Uvicorn
   +
psutil
   +
smartmontools
   +
systemd
   +
HTML/CSS/JavaScript
```

into a single dashboard for monitoring the health and availability of a home server.