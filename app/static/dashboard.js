const REFRESH_INTERVAL = 5000;


function $(id) {
    return document.getElementById(id);
}


function formatNumber(value, decimals = 1) {
    if (value === null || value === undefined) {
        return "—";
    }

    return Number(value).toFixed(decimals);
}


function setProgress(id, value) {
    const element = $(id);

    if (!element) {
        return;
    }

    const safe = Math.max(0, Math.min(100, Number(value) || 0));

    element.style.width = `${safe}%`;
}


function setStatus(element, text, state) {

    element.textContent = text;

    element.className = "status-pill";

    if (state === "good") {
        element.classList.add("status-good");
    } else if (state === "warning") {
        element.classList.add("status-warning");
    } else if (state === "danger") {
        element.classList.add("status-danger");
    } else {
        element.classList.add("status-loading");
    }
}


function updateSystem(system) {

    $("cpu-usage").textContent =
        `${formatNumber(system.cpu_usage)}%`;

    setProgress(
        "cpu-bar",
        system.cpu_usage
    );


    $("cpu-temp").textContent =
        system.cpu_temperature !== null
            ? `${formatNumber(system.cpu_temperature, 0)}°C`
            : "—";


    $("ram-usage").textContent =
        `${formatNumber(system.ram_usage)}%`;

    $("ram-detail").textContent =
        `${formatNumber(system.ram_used_gb, 2)} GB / ${formatNumber(system.ram_total_gb, 2)} GB`;

    setProgress(
        "ram-bar",
        system.ram_usage
    );


    $("storage-usage").textContent =
        `${formatNumber(system.storage_usage)}%`;

    $("storage-detail").textContent =
        `${formatNumber(system.storage_used_gb, 2)} GB used • ${formatNumber(system.storage_free_gb, 2)} GB free`;

    setProgress(
        "storage-bar",
        system.storage_usage
    );
}


function updateNetwork(network) {

    const internetOnline =
        network.internet_status === "ONLINE";

    const routerOnline =
        network.router_status === "ONLINE";


    $("internet-status").textContent =
        internetOnline ? "Online" : "Offline";

    $("internet-status").style.color =
        internetOnline
            ? "var(--green)"
            : "var(--red)";


    $("internet-ping").textContent =
        network.internet_ping_ms !== null
            ? `${formatNumber(network.internet_ping_ms)} ms`
            : "No response";


    $("router-status").textContent =
        routerOnline ? "Online" : "Offline";

    $("router-status").style.color =
        routerOnline
            ? "var(--green)"
            : "var(--red)";


    $("router-ping").textContent =
        network.router_ping_ms !== null
            ? `${formatNumber(network.router_ping_ms)} ms`
            : "No response";
}


function driveSeverity(drive) {

    if (
        (drive.pending || 0) > 0 ||
        (drive.offline_uncorrectable || 0) > 0
    ) {
        return "danger";
    }


    if ((drive.reallocated || 0) > 0) {
        return "warning";
    }


    if (drive.health !== "OK") {
        return "warning";
    }


    return "good";
}


function driveBadge(severity) {

    if (severity === "danger") {
        return ["CRITICAL", "badge-danger"];
    }

    if (severity === "warning") {
        return ["WARNING", "badge-warning"];
    }

    return ["HEALTHY", "badge-good"];
}


function createDriveCard(name, drive) {

    const severity = driveSeverity(drive);

    const [badgeText, badgeClass] =
        driveBadge(severity);


    let warning = "";


    if (
        (drive.pending || 0) > 0 ||
        (drive.offline_uncorrectable || 0) > 0
    ) {

        warning =
            `This drive has sectors requiring attention. ` +
            `Do not rely on it as the only copy of important data.`;
    }
    else if ((drive.reallocated || 0) > 0) {

        warning =
            `The drive has previously reallocated sectors. ` +
            `Continue monitoring SMART values.`;
    }


    return `
        <div class="card drive-card">

            <div class="drive-header">

                <div>
                    <div class="drive-name">
                        ${name.toUpperCase()}
                    </div>

                    <div class="drive-device">
                        /dev/${name}
                    </div>
                </div>

                <div class="drive-badge ${badgeClass}">
                    ${badgeText}
                </div>

            </div>


            <div class="drive-temp">

                <div class="drive-temp-value">
                    ${drive.temperature ?? "—"}°C
                </div>

                <div class="drive-temp-label">
                    Temperature
                </div>

            </div>


            <div class="drive-stats">

                <div class="drive-stat">
                    <div class="drive-stat-label">
                        Reallocated
                    </div>

                    <div class="drive-stat-value">
                        ${drive.reallocated ?? "—"}
                    </div>
                </div>


                <div class="drive-stat">
                    <div class="drive-stat-label">
                        Pending
                    </div>

                    <div class="drive-stat-value">
                        ${drive.pending ?? "—"}
                    </div>
                </div>


                <div class="drive-stat">
                    <div class="drive-stat-label">
                        Uncorrectable
                    </div>

                    <div class="drive-stat-value">
                        ${drive.offline_uncorrectable ?? "—"}
                    </div>
                </div>


                <div class="drive-stat">
                    <div class="drive-stat-label">
                        CRC Errors
                    </div>

                    <div class="drive-stat-value">
                        ${drive.crc_errors ?? "—"}
                    </div>
                </div>

            </div>


            ${
                warning
                    ? `<div class="drive-warning">
                        ⚠ ${warning}
                       </div>`
                    : ""
            }

        </div>
    `;
}


function updateDrives(smart) {

    const container = $("drives");

    container.innerHTML = "";


    const drives = smart.drives || {};

    for (const [name, drive] of Object.entries(drives)) {

        container.insertAdjacentHTML(
            "beforeend",
            createDriveCard(name, drive)
        );
    }


    if (!Object.keys(drives).length) {

        container.innerHTML =
            `<div class="card loading-card">
                No drive data available.
             </div>`;
    }


    $("smart-update").textContent =
        `SMART cache: ${smart.interval_seconds / 60} min`;
}


function updateArduino(arduino) {

    const active = arduino.active;

    $("arduino-status").textContent =
        active ? "Running" : "Stopped";

    $("arduino-status").style.color =
        active
            ? "var(--green)"
            : "var(--red)";
}


function updateOverallStatus(data) {

    const element = $("overall-status");

    const drives =
        data.smart?.drives || {};

    const criticalDrive =
        Object.values(drives).some(
            drive =>
                (drive.pending || 0) > 0 ||
                (drive.offline_uncorrectable || 0) > 0
        );


    const networkDown =
        data.network?.internet_status !== "ONLINE";


    if (criticalDrive) {

        setStatus(
            element,
            "Drive Attention",
            "danger"
        );

        return;
    }


    if (networkDown) {

        setStatus(
            element,
            "Network Issue",
            "warning"
        );

        return;
    }


    setStatus(
        element,
        "System Operational",
        "good"
    );
}


async function refreshDashboard() {

    try {

        const response =
            await fetch(
                "/api/dashboard",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        updateSystem(data.system);

        updateNetwork(data.network);

        updateDrives(data.smart);

        updateArduino(data.arduino);

        updateOverallStatus(data);


        $("last-update").textContent =
            new Date().toLocaleTimeString();


    } catch (error) {

        console.error(
            "Dashboard refresh failed:",
            error
        );


        setStatus(
            $("overall-status"),
            "Backend Offline",
            "danger"
        );
    }
}


refreshDashboard();


setInterval(
    refreshDashboard,
    REFRESH_INTERVAL
);
