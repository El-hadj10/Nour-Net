const defaultDorks = [
  "URL Redirection nph-proxy",
  "Simple PHP Proxy script",
  "index of /cgi-bin/nph-proxy",
  "CGI Proxy Server error"
];

const form = document.getElementById("session-form");
const launchBtn = document.getElementById("launch-btn");
const stopBtn = document.getElementById("stop-btn");
const exportJsonBtn = document.getElementById("export-json-btn");
const exportCsvBtn = document.getElementById("export-csv-btn");
const clearLogsBtn = document.getElementById("clear-logs-btn");
const logFilterSelect = document.getElementById("log-filter");
const dorksInput = document.getElementById("dorks");
const limitInput = document.getElementById("limit");
const proxyInput = document.getElementById("proxy");
const pauseMinInput = document.getElementById("pause-min");
const pauseMaxInput = document.getElementById("pause-max");
const checkTorInput = document.getElementById("check-tor");

const statusEl = document.getElementById("status");
const foundEl = document.getElementById("found");
const aliveEl = document.getElementById("alive");
const deadEl = document.getElementById("dead");
const footerLine = document.getElementById("footer-line");
const sessionList = document.getElementById("session-list");

const logStream = document.getElementById("log-stream");
const mapCanvas = document.getElementById("map-canvas");
const mapCaption = document.getElementById("map-caption");

const map = L.map("map-canvas", {
  zoomControl: true,
  attributionControl: true,
}).setView([20, 0], 2);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const markerLayer = L.layerGroup().addTo(map);

let ws = null;
let currentSessionId = null;
let aliveTargets = [];
let markerCount = 0;
let mapBounds = null;
let currentLogFilter = "all";
let counters = {
  found: 0,
  alive: 0,
  dead: 0,
};

dorksInput.value = defaultDorks.join("\n");

function appendLog(level, message) {
  const line = document.createElement("div");
  const normalizedLevel = level || "info";
  line.className = `log-line ${normalizedLevel}`;
  line.dataset.level = normalizedLevel;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

  if (currentLogFilter !== "all" && normalizedLevel !== currentLogFilter) {
    line.classList.add("hidden");
  }

  logStream.appendChild(line);
  logStream.scrollTop = logStream.scrollHeight;

  while (logStream.children.length > 500) {
    logStream.removeChild(logStream.firstChild);
  }
}

function setStatus(text) {
  statusEl.className = "";
  statusEl.classList.add(text);
  statusEl.textContent = text;
  footerLine.textContent = `session: ${text}`;
}

function applyLogFilter(filterValue) {
  currentLogFilter = filterValue;
  const lines = logStream.querySelectorAll(".log-line");
  lines.forEach((line) => {
    const level = line.dataset.level || "info";
    const visible = filterValue === "all" || level === filterValue;
    line.classList.toggle("hidden", !visible);
  });
}

function resetCounters() {
  counters = { found: 0, alive: 0, dead: 0 };
  foundEl.textContent = "0";
  aliveEl.textContent = "0";
  deadEl.textContent = "0";
}

function clearMap() {
  markerLayer.clearLayers();
  markerCount = 0;
  mapBounds = null;
  map.setView([20, 0], 2);
  mapCaption.textContent = "Aucun noeud valide pour cette session.";
}

function updateMapCaption() {
  if (!markerCount) {
    mapCaption.textContent = "Aucun noeud valide pour cette session.";
    return;
  }
  mapCaption.textContent = `${markerCount} noeuds geolocalises pour cette session.`;
}

function maybeEnableSessionActions() {
  const hasSession = Boolean(currentSessionId);
  exportJsonBtn.disabled = !hasSession;
  exportCsvBtn.disabled = !hasSession;
}

async function geolocateAndPlot(url) {
  if (!url) {
    return;
  }

  try {
    const response = await fetch(`/api/geolocate?target_url=${encodeURIComponent(url)}`);
    if (!response.ok) {
      return;
    }
    const payload = await response.json();
    if (!payload.ok || typeof payload.lat !== "number" || typeof payload.lon !== "number") {
      return;
    }

    const popup = `
      <strong>${payload.host || "host"}</strong><br>
      ${payload.city || "-"}, ${payload.country || "-"}<br>
      IP: ${payload.ip || "-"}
    `;

    const marker = L.circleMarker([payload.lat, payload.lon], {
      radius: 6,
      color: "#72f1b4",
      fillColor: "#72f1b4",
      fillOpacity: 0.7,
      weight: 1,
    }).bindPopup(popup);

    markerLayer.addLayer(marker);
    markerCount += 1;
    const latLng = L.latLng(payload.lat, payload.lon);
    if (!mapBounds) {
      mapBounds = L.latLngBounds(latLng, latLng);
    } else {
      mapBounds.extend(latLng);
    }
    updateMapCaption();

    if (markerCount === 1) {
      map.setView([payload.lat, payload.lon], 3);
    } else if (mapBounds) {
      map.fitBounds(mapBounds, { padding: [30, 30], maxZoom: 5 });
    }
  } catch (_err) {
    // Ignore geolocation failures to keep live stream smooth.
  }
}

async function exportCurrentSession(format) {
  if (!currentSessionId) {
    return;
  }

  try {
    const response = await fetch(`/api/sessions/${currentSessionId}/export?format=${format}`);
    if (!response.ok) {
      throw new Error("export impossible");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `nour-session-${currentSessionId}.${format}`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
    appendLog("success", `Export ${format.toUpperCase()} termine.`);
  } catch (err) {
    appendLog("error", `Erreur export ${format.toUpperCase()}: ${err.message}`);
  }
}

async function stopCurrentSession() {
  if (!currentSessionId) {
    return;
  }

  try {
    const response = await fetch(`/api/sessions/${currentSessionId}/stop`, {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error("arret refuse");
    }
    const payload = await response.json();
    appendLog("warning", `Stop demande pour ${payload.session_id}.`);
    stopBtn.disabled = true;
  } catch (err) {
    appendLog("error", `Erreur stop: ${err.message}`);
  }
}

function setActionStates(statusText) {
  const isRunning = ["session_start", "dork_start", "running", "session_queued"].includes(statusText);
  stopBtn.disabled = !currentSessionId || !isRunning;
  maybeEnableSessionActions();
}

function handleEvent(eventPayload) {
  const eventType = eventPayload.event;
  const level = eventPayload.level || "info";
  const message = eventPayload.message || eventType;
  const data = eventPayload.data || {};

  if (eventType !== "SNAPSHOT") {
    appendLog(level, message);
  }

  if (eventType === "TARGET_FOUND") {
    counters.found += 1;
    foundEl.textContent = String(counters.found);
  }

  if (eventType === "TARGET_VALIDATED") {
    if (data.alive) {
      counters.alive += 1;
      aliveTargets.push(data.url || "");
      geolocateAndPlot(data.url || "");
    } else {
      counters.dead += 1;
    }
    aliveEl.textContent = String(counters.alive);
    deadEl.textContent = String(counters.dead);
  }

  if (["SESSION_START", "DORK_START", "SESSION_DONE", "SESSION_ABORTED", "SESSION_FAILED", "SESSION_EMPTY"].includes(eventType)) {
    setStatus(eventType.toLowerCase());
    setActionStates(eventType.toLowerCase());
  }

  if (["SESSION_DONE", "SESSION_ABORTED", "SESSION_FAILED", "SESSION_STOPPED", "SESSION_EMPTY"].includes(eventType)) {
    stopBtn.disabled = true;
  }

  if (eventType === "SESSION_EMPTY") {
    mapCaption.textContent = message;
  }

  if (eventType === "SESSION_DONE" && data.summary) {
    foundEl.textContent = String(data.summary.targets_found || counters.found);
    aliveEl.textContent = String(data.summary.alive || counters.alive);
    deadEl.textContent = String(data.summary.dead || counters.dead);
  }
}

async function refreshSessionList() {
  try {
    const response = await fetch("/api/sessions");
    const payload = await response.json();
    const sessions = payload.sessions || [];

    sessionList.innerHTML = "";
    sessions.forEach((session) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${session.session_id}</span><span>${session.status}</span>`;
      li.addEventListener("click", () => attachToSession(session.session_id));
      sessionList.appendChild(li);
    });
  } catch (_err) {
    appendLog("error", "Impossible de charger la liste des sessions.");
  }
}

function attachToSession(sessionId) {
  if (!sessionId) {
    return;
  }

  if (ws) {
    ws.close();
  }

  currentSessionId = sessionId;
  aliveTargets = [];
  clearMap();
  maybeEnableSessionActions();
  stopBtn.disabled = false;

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${protocol}://${window.location.host}/api/sessions/${sessionId}/ws`);

  ws.onopen = () => {
    appendLog("info", `Connecte a la session ${sessionId}`);
  };

  ws.onmessage = (evt) => {
    const payload = JSON.parse(evt.data);
    if (payload.event === "SNAPSHOT") {
      resetCounters();
      logStream.innerHTML = "";
      const events = (payload.data && payload.data.events) || [];
      events.forEach((eventItem) => handleEvent(eventItem));
      return;
    }
    handleEvent(payload);
  };

  ws.onclose = () => {
    appendLog("warning", `Stream termine pour la session ${sessionId}`);
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  launchBtn.disabled = true;

  const dorks = dorksInput.value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

  const payload = {
    dorks,
    per_dork_limit: Number(limitInput.value),
    proxy: proxyInput.value.trim(),
    pause_min: Number(pauseMinInput.value),
    pause_max: Number(pauseMaxInput.value),
    check_tor: checkTorInput.checked,
  };

  try {
    resetCounters();
    aliveTargets = [];
    clearMap();
    logStream.innerHTML = "";

    const response = await fetch("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorPayload = await response.json();
      throw new Error(errorPayload.detail || "creation session impossible");
    }

    const data = await response.json();
    appendLog("success", `Session ${data.session_id} creee.`);
    attachToSession(data.session_id);
    stopBtn.disabled = false;
    await refreshSessionList();
  } catch (err) {
    appendLog("error", `Erreur: ${err.message}`);
  } finally {
    launchBtn.disabled = false;
  }
});

stopBtn.addEventListener("click", stopCurrentSession);
exportJsonBtn.addEventListener("click", () => exportCurrentSession("json"));
exportCsvBtn.addEventListener("click", () => exportCurrentSession("csv"));
clearLogsBtn.addEventListener("click", () => {
  logStream.innerHTML = "";
});
logFilterSelect.addEventListener("change", (event) => {
  applyLogFilter(event.target.value);
});

clearMap();
maybeEnableSessionActions();
applyLogFilter("all");
refreshSessionList();
setInterval(refreshSessionList, 10000);
